<?php

namespace App\Services;

use App\Models\Question;
use App\Models\QuizAttempt;
use Illuminate\Database\Eloquent\Collection;
use Illuminate\Support\Facades\DB;
use Illuminate\Support\Str;
use Illuminate\Validation\ValidationException;

class QuizEngine
{
    public function eligible(array $filters = []): Collection
    {
        $query = Question::with('sign')->where('status', 'published')->whereNotNull('reviewed_at')
            ->where(function ($query): void {
                $query->whereNull('sign_id')->orWhereHas('sign', fn ($sign) => $sign->where('status', 'published')->whereNotNull('image_path'));
            });
        if (! empty($filters['class'])) {
            $query->where('class_code', $filters['class'])->where('topic', '!=', 'classes');
        }
        if (! empty($filters['subcategory'])) {
            $query->where('subcategory_id', $filters['subcategory'])->where('topic', '!=', 'subcategories');
        }
        if (($filters['topic'] ?? 'mixed') !== 'mixed') {
            $query->where('topic', $filters['topic']);
        }
        $questions = $query->orderBy('id')->get();
        $groupCounts = Question::whereNotNull('group_key')->selectRaw('group_key, count(*) as total')->groupBy('group_key')->pluck('total', 'group_key');
        $included = $questions->whereNotNull('group_key')->countBy('group_key');

        return $questions->filter(fn ($q) => ! $q->group_key || ($included[$q->group_key] ?? 0) === (int) ($groupCounts[$q->group_key] ?? 0))->values();
    }

    public function blueprint(array $filters, Collection $pool): array
    {
        $length = (int) $filters['length'];
        if ($filters['topic'] !== 'mixed') {
            return [$filters['topic'] => $length];
        }
        $plan = config('quiz.blueprint');
        if (! $pool->contains('topic', 'general')) {
            $plan['names'] += $plan['general'];
            unset($plan['general']);
        }
        if (! empty($filters['class'])) {
            $plan['names'] += $plan['classes'];
            unset($plan['classes']);
        }
        if (! empty($filters['subcategory']) || ($filters['class'] ?? null) === 'B') {
            $plan['names'] += $plan['subcategories'];
            unset($plan['subcategories']);
        }

        return array_map(fn ($count) => $count * ($length / 10), $plan);
    }

    public function start(string $owner, array $filters): QuizAttempt
    {
        $pool = $this->eligible($filters);
        $plan = $this->blueprint($filters, $pool);
        $units = $pool->groupBy(fn ($q) => $q->group_key ? 'group:'.$q->group_key : 'question:'.$q->id)->values();
        $selected = null;
        // Randomised whole-group selection; never repeat a question or independent sign.
        for ($trial = 0; $trial < 100; $trial++) {
            $remaining = $plan;
            $usedSigns = [];
            $chosen = collect();
            foreach ($units->shuffle() as $unit) {
                $counts = $unit->countBy('topic');
                $signs = $unit->pluck('sign_id')->filter()->unique()->all();
                if (array_intersect($signs, $usedSigns)) {
                    continue;
                }
                if ($counts->contains(fn ($count, $topic) => $count > ($remaining[$topic] ?? 0))) {
                    continue;
                }
                foreach ($counts as $topic => $count) {
                    $remaining[$topic] -= $count;
                }
                $usedSigns = array_merge($usedSigns, $signs);
                $chosen = $chosen->concat($unit->sortBy('group_order'));
                if (array_sum($remaining) === 0) {
                    $selected = $chosen;
                    break 2;
                }
            }
        }
        if ($selected === null) {
            throw ValidationException::withMessages(['length' => 'There are not enough compatible reviewed questions for this mix. Choose another topic/filter or add reviewed questions; no draft content or repeated questions will be substituted.']);
        }
        $items = $selected->map(function ($q): array {
            $options = collect($q->options);
            if ($q->shuffle_options) {
                $options = $options->shuffle();
            }

            return [
                'id' => $q->id, 'version' => $q->version, 'prompt' => $q->prompt, 'topic' => $q->topic,
                'type' => $q->type, 'options' => $options->values()->all(), 'correct_ids' => $q->correct_ids,
                'explanation' => $q->explanation, 'sign_id' => $q->sign_id, 'group_key' => $q->group_key,
                'image_url' => $q->sign_id ? route('api.signs.image', ['id' => $q->sign_id]) : null,
            ];
        })->values()->all();

        return QuizAttempt::create([
            'owner_hash' => $owner, 'public_id' => (string) Str::uuid(), 'status' => 'active', 'mode' => $filters['mode'], 'topic' => $filters['topic'],
            'filters' => $filters + ['blueprint' => $plan, 'scoring' => 'exact-set-v1'], 'items' => $items, 'answers' => [], 'total' => count($items),
            'started_at' => now(), 'expires_at' => $filters['mode'] === 'challenge' ? now()->addSeconds(config('quiz.challenge_seconds')) : now()->addHours(config('quiz.practice_hours')),
        ]);
    }

    public function matches(array $selected, array $correct): bool
    {
        sort($selected);
        sort($correct);

        return $selected === $correct;
    }

    public function finish(QuizAttempt $attempt, string $status): void
    {
        if ($attempt->status !== 'active') {
            return;
        }
        $answers = $attempt->answers;
        $score = 0;
        foreach ($attempt->items as $item) {
            $answer = $answers[$item['id']] ?? null;
            if ($answer && $this->matches($answer['selected_ids'], $item['correct_ids'])) {
                $score++;
            }
        }
        $attempt->update(['status' => $status, 'score' => $score, 'completed_at' => now()]);
    }

    public function access(string $id, string $owner, ?array $answer = null, bool $complete = false): QuizAttempt
    {
        return DB::transaction(function () use ($id, $owner, $answer, $complete): QuizAttempt {
            $attempt = QuizAttempt::where('id', $id)->where('owner_hash', $owner)->lockForUpdate()->firstOrFail();
            if ($attempt->status === 'active' && now()->greaterThanOrEqualTo($attempt->expires_at)) {
                $this->finish($attempt, 'expired');
            }
            if ($attempt->status !== 'active') {
                return $attempt;
            }
            if ($answer !== null) {
                $item = collect($attempt->items)->firstWhere('id', $answer['question_id']);
                if (! $item || array_diff($answer['selected_ids'], array_column($item['options'], 'id')) || ($item['type'] === 'single' && count($answer['selected_ids']) > 1)) {
                    throw ValidationException::withMessages(['selected_ids' => 'Choose valid options from this question.']);
                }
                $answers = $attempt->answers;
                if ($attempt->mode === 'practice' && isset($answers[$item['id']])) {
                    return $attempt;
                }
                if ($attempt->mode === 'practice' && ! $answer['selected_ids']) {
                    throw ValidationException::withMessages(['selected_ids' => 'Choose an answer before checking it.']);
                }
                $answers[$item['id']] = ['selected_ids' => $answer['selected_ids'], 'saved_at' => now()->toIso8601String()];
                $attempt->update(['answers' => $answers]);
            }
            if ($complete) {
                $this->finish($attempt, 'completed');
            }

            return $attempt;
        });
    }

    public function present(QuizAttempt $attempt): array
    {
        $answers = $attempt->answers;
        $items = collect($attempt->items)->map(function ($item) use ($attempt, $answers): array {
            $answer = $answers[$item['id']] ?? null;
            $groupDone = ! $item['group_key'] || collect($attempt->items)->where('group_key', $item['group_key'])->every(fn ($q) => isset($answers[$q['id']]));
            $show = $attempt->status !== 'active' || ($attempt->mode === 'practice' && $answer && $groupDone);
            $safe = array_diff_key($item, array_flip(['correct_ids', 'explanation', 'group_key', 'sign_id']));
            $safe['selected_ids'] = $answer['selected_ids'] ?? [];
            $safe['locked'] = $attempt->status !== 'active' || ($attempt->mode === 'practice' && $answer !== null);
            $safe['feedback_pending'] = $attempt->mode === 'practice' && $answer && ! $groupDone;
            if ($show) {
                $safe['correct_ids'] = $item['correct_ids'];
                $safe['explanation'] = $item['explanation'];
                $safe['correct'] = $answer && $this->matches($answer['selected_ids'], $item['correct_ids']);
            }

            return $safe;
        })->all();

        return [
            'id' => $attempt->id, 'mode' => $attempt->mode, 'topic' => $attempt->topic, 'filters' => $attempt->filters,
            'status' => $attempt->status, 'total' => $attempt->total, 'score' => $attempt->score, 'items' => $items,
            'started_at' => $attempt->started_at->toIso8601String(), 'expires_at' => $attempt->expires_at->toIso8601String(),
            'server_now' => now()->toIso8601String(), 'completed_at' => $attempt->completed_at?->toIso8601String(),
            'share_url' => $attempt->status !== 'active' ? route('quiz.result', ['publicId' => $attempt->public_id]) : null,
        ];
    }
}
