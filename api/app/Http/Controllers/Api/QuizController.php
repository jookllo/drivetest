<?php

namespace App\Http\Controllers\Api;

use App\Http\Controllers\Controller;
use App\Http\Requests\StartQuizRequest;
use App\Http\Resources\QuizAttemptResource;
use App\Models\QuizAttempt;
use App\Services\QuizEngine;
use Illuminate\Http\JsonResponse;
use Illuminate\Http\Request;
use Illuminate\Support\Str;

class QuizController extends Controller
{
    public function __construct(private QuizEngine $engine) {}

    private function owner(Request $request): string
    {
        if (! $request->session()->has('quiz_guest')) {
            $request->session()->put('quiz_guest', Str::random(64));
        }

        return hash('sha256', $request->session()->get('quiz_guest'));
    }

    public function session(Request $request): JsonResponse
    {
        $attempt = QuizAttempt::where('owner_hash', $this->owner($request))->latest()->first();

        return response()->json(['csrf_token' => csrf_token(), 'attempt' => $attempt ? $this->engine->present($this->engine->access($attempt->id, $this->owner($request))) : null]);
    }

    public function topics(Request $request): JsonResponse
    {
        $filters = $request->validate(['class' => 'nullable|in:A,B,C', 'subcategory' => 'nullable|string|max:40']);
        $pool = $this->engine->eligible($filters);

        return response()->json(['data' => collect(config('quiz.topics'))->map(fn ($label, $id) => ['id' => $id, 'label' => $label, 'count' => $pool->where('topic', $id)->count()])->values(), 'classes' => config('signs.classes'), 'lengths' => config('quiz.lengths'), 'challenge_seconds' => config('quiz.challenge_seconds')]);
    }

    public function store(StartQuizRequest $request): QuizAttemptResource
    {
        return new QuizAttemptResource($this->engine->start($this->owner($request), $request->validated()));
    }

    public function show(Request $request, string $id): QuizAttemptResource
    {
        return new QuizAttemptResource($this->engine->access($id, $this->owner($request)));
    }

    public function answer(Request $request, string $id): QuizAttemptResource
    {
        $data = $request->validate(['question_id' => 'required|uuid', 'selected_ids' => 'present|array|max:6', 'selected_ids.*' => 'required|string|max:40|distinct']);

        return new QuizAttemptResource($this->engine->access($id, $this->owner($request), $data));
    }

    public function complete(Request $request, string $id): QuizAttemptResource
    {
        return new QuizAttemptResource($this->engine->access($id, $this->owner($request), complete: true));
    }

    public function result(string $publicId): JsonResponse
    {
        $attempt = QuizAttempt::where('public_id', $publicId)->where('status', '!=', 'active')->firstOrFail();

        return response()->json(['data' => ['score' => $attempt->score, 'total' => $attempt->total, 'topic' => $attempt->topic, 'mode' => $attempt->mode, 'status' => $attempt->status, 'completed_at' => $attempt->completed_at->toIso8601String()]]);
    }
}
