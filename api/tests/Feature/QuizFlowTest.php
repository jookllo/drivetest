<?php

namespace Tests\Feature;

use App\Models\Question;
use App\Models\QuizAttempt;
use App\Services\QuizEngine;
use Illuminate\Foundation\Testing\RefreshDatabase;
use Tests\TestCase;

class QuizFlowTest extends TestCase
{
    use RefreshDatabase;

    protected function setUp(): void
    {
        parent::setUp();
        $this->assertSame('drivetest_test', config('database.connections.mysql.database'), 'Never run destructive database tests on the application database.');
    }

    private function start(string $mode = 'practice'): array
    {
        return $this->withSession(['quiz_guest' => 'guest-one'])->postJson('/api/v1/quiz-attempts', ['mode' => $mode, 'topic' => 'general', 'length' => 10])->assertCreated()->json('data');
    }

    public function test_guests_get_saved_attempts_without_answer_keys_and_other_guests_cannot_read_them(): void
    {
        Question::factory()->published()->count(10)->create();
        $a = $this->start();
        $this->assertCount(10, $a['items']);
        $this->assertArrayNotHasKey('correct_ids', $a['items'][0]);
        $this->assertArrayNotHasKey('explanation', $a['items'][0]);
        $this->assertNull($a['share_url']);
        $this->withSession(['quiz_guest' => 'guest-one'])->getJson('/api/v1/quiz-session')->assertOk()->assertJsonPath('attempt.id', $a['id']);
        $this->withSession(['quiz_guest' => 'guest-two'])->getJson('/api/v1/quiz-attempts/'.$a['id'])->assertNotFound();
        $this->withSession(['quiz_guest' => 'guest-two'])->postJson('/api/v1/quiz-attempts/'.$a['id'].'/complete')->assertNotFound();
    }

    public function test_practice_marks_on_server_locks_answers_and_survives_question_edits(): void
    {
        Question::factory()->published()->count(10)->create();
        $a = $this->start();
        $q = $a['items'][0]['id'];
        Question::findOrFail($q)->update(['correct_ids' => ['b'], 'explanation' => 'Changed later']);
        $this->postJson('/api/v1/quiz-attempts/'.$a['id'].'/answers', ['question_id' => $q, 'selected_ids' => ['a']])->assertOk()->assertJsonPath('data.items.0.correct', true)->assertJsonPath('data.items.0.explanation', 'Reviewed explanation.');
        $this->postJson('/api/v1/quiz-attempts/'.$a['id'].'/answers', ['question_id' => $q, 'selected_ids' => ['b']])->assertOk()->assertJsonPath('data.items.0.selected_ids.0', 'a');
        $r = $this->postJson('/api/v1/quiz-attempts/'.$a['id'].'/complete')->assertOk()->assertJsonPath('data.score', 1)->json('data');
        $this->postJson('/api/v1/quiz-attempts/'.$a['id'].'/complete')->assertJsonPath('data.score', 1);
        $this->get($r['share_url'])->assertOk()->assertSee('1/10 on DriveTest');
        $public = QuizAttempt::findOrFail($a['id'])->public_id;
        $this->getJson('/api/v1/results/'.$public)->assertOk()->assertJsonMissingPath('data.items')->assertJsonMissingPath('data.owner_hash')->assertJsonMissingPath('data.id');
    }

    public function test_timed_answers_stay_private_until_exact_deadline_and_late_answers_are_ignored(): void
    {
        Question::factory()->published()->count(10)->create();
        $this->freezeTime();
        $a = $this->start('challenge');
        $q = $a['items'][0]['id'];
        $this->postJson('/api/v1/quiz-attempts/'.$a['id'].'/answers', ['question_id' => $q, 'selected_ids' => ['a']])->assertOk()->assertJsonMissingPath('data.items.0.correct_ids');
        $this->travel(299)->seconds();
        $this->getJson('/api/v1/quiz-attempts/'.$a['id'])->assertJsonPath('data.status', 'active')->assertJsonPath('data.expires_at', $a['expires_at']);
        $this->travel(1)->seconds();
        $this->postJson('/api/v1/quiz-attempts/'.$a['id'].'/answers', ['question_id' => $q, 'selected_ids' => ['b']])->assertOk()->assertJsonPath('data.status', 'expired')->assertJsonPath('data.score', 1);
        $this->getJson('/api/v1/quiz-attempts/'.$a['id'])->assertJsonPath('data.score', 1)->assertJsonPath('data.items.0.selected_ids.0', 'a');
    }

    public function test_multiple_answers_require_exact_set_and_invalid_option_ids_are_rejected(): void
    {
        Question::factory()->published()->count(10)->create(['type' => 'multi', 'options' => [['id' => 'a', 'label' => 'A'], ['id' => 'b', 'label' => 'B'], ['id' => 'c', 'label' => 'C']], 'correct_ids' => ['a', 'b']]);
        $a = $this->start();
        $q = $a['items'][0]['id'];
        $this->postJson('/api/v1/quiz-attempts/'.$a['id'].'/answers', ['question_id' => $q, 'selected_ids' => ['unknown']])->assertUnprocessable();
        $this->postJson('/api/v1/quiz-attempts/'.$a['id'].'/answers', ['question_id' => $q, 'selected_ids' => ['a', 'a']])->assertUnprocessable();
        $this->postJson('/api/v1/quiz-attempts/'.$a['id'].'/answers', ['question_id' => $q, 'selected_ids' => ['a']])->assertJsonPath('data.items.0.correct', false);
        $engine = app(QuizEngine::class);
        $this->assertTrue($engine->matches(['b', 'a'], ['a', 'b']));
        $this->assertFalse($engine->matches(['a', 'b', 'c'], ['a', 'b']));
    }

    public function test_drafts_and_short_pools_are_not_silently_used(): void
    {
        Question::factory()->count(20)->create();
        Question::factory()->published()->count(9)->create();
        $this->withSession(['quiz_guest' => 'x'])->postJson('/api/v1/quiz-attempts', ['mode' => 'practice', 'topic' => 'general', 'length' => 10])->assertUnprocessable();
        $this->assertDatabaseCount('quiz_attempts', 0);
        $this->getJson('/api/v1/quiz-topics')->assertJsonPath('data.3.count', 9);
    }

    public function test_mixed_blueprint_and_group_feedback_are_respected(): void
    {
        foreach (['names' => 4, 'classes' => 2, 'subcategories' => 2, 'general' => 2] as $topic => $count) {
            Question::factory()->published()->count($count)->create(['topic' => $topic]);
        }
        $this->withSession(['quiz_guest' => 'x']);
        $a = $this->postJson('/api/v1/quiz-attempts', ['mode' => 'practice', 'topic' => 'mixed', 'length' => 10])->assertCreated()->json('data');
        $counts = collect($a['items'])->countBy('topic')->all();
        $this->assertEquals(['names' => 4, 'classes' => 2, 'subcategories' => 2, 'general' => 2], $counts);
        $this->assertCount(10, array_unique(array_column($a['items'], 'id')));
        Question::query()->delete();
        $group = Question::factory()->published()->count(2)->create(['group_key' => 'group']);
        Question::factory()->published()->count(8)->create();
        $a = $this->start();
        $q = $group[0]->id;
        $answer = $this->postJson('/api/v1/quiz-attempts/'.$a['id'].'/answers', ['question_id' => $q, 'selected_ids' => ['a']])->assertOk()->json('data.items');
        $first = collect($answer)->firstWhere('id', $q);
        $this->assertTrue($first['feedback_pending']);
        $this->assertArrayNotHasKey('correct_ids', $first);
        $answer = $this->postJson('/api/v1/quiz-attempts/'.$a['id'].'/answers', ['question_id' => $group[1]->id, 'selected_ids' => ['a']])->assertOk()->json('data.items');
        $this->assertArrayHasKey('correct_ids', collect($answer)->firstWhere('id', $q));
    }
}
