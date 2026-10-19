<?php

namespace Tests\Feature;

use App\Models\Question;
use App\Models\Sign;
use App\Models\User;
use Illuminate\Foundation\Testing\RefreshDatabase;
use Tests\TestCase;

class QuizSecurityTest extends TestCase
{
    use RefreshDatabase;

    protected function setUp(): void
    {
        parent::setUp();
        $this->assertSame('drivetest_test', config('database.connections.mysql.database'));
    }

    public function test_production_redirects_http_and_sets_hsts_for_https(): void
    {
        $this->app->instance('env', 'production');
        $this->get('http://localhost/quiz')->assertStatus(308)->assertRedirect('https://localhost/quiz');
        $this->get('https://localhost/quiz')->assertOk()->assertHeader('Strict-Transport-Security', 'max-age=31536000');
    }

    public function test_sign_edits_invalidate_linked_question_publication(): void
    {
        $this->actingAs(User::factory()->create(['is_admin' => true]));
        $sign = Sign::factory()->create();
        $q = Question::factory()->published()->create(['sign_id' => $sign->id]);
        $this->putJson('/api/v1/admin/signs/'.$sign->id, ['name' => 'New name', 'meaning' => null, 'class_code' => 'B', 'subcategory_id' => null, 'status' => 'draft', 'review_notes' => null, 'reviewed' => false, 'updated_at' => $sign->updated_at->toJSON()])->assertOk();
        $this->assertDatabaseHas('questions', ['id' => $q->id, 'status' => 'draft', 'reviewed_at' => null]);
    }

    public function test_import_validates_whole_batch_and_creates_drafts(): void
    {
        $path = tempnam(sys_get_temp_dir(), 'quiz-import-');
        $payload = ['prompt' => 'Imported question?', 'topic' => 'general', 'type' => 'single', 'options' => [['id' => 'a', 'label' => 'A'], ['id' => 'b', 'label' => 'B']], 'correct_ids' => ['a'], 'explanation' => 'A is correct.', 'status' => 'published', 'reviewed' => true];
        try {
            file_put_contents($path, json_encode([$payload]));
            $this->artisan('questions:import', ['file' => $path, '--dry-run' => true])->assertSuccessful();
            $this->assertDatabaseCount('questions', 0);
            $this->artisan('questions:import', ['file' => $path])->assertSuccessful();
            $this->assertDatabaseHas('questions', ['prompt' => 'Imported question?', 'status' => 'draft', 'reviewed_at' => null]);
            $this->artisan('questions:import', ['file' => $path])->assertFailed();
            $this->assertDatabaseCount('questions', 1);
        } finally {
            unlink($path);
        }
    }
}
