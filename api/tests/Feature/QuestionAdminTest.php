<?php

namespace Tests\Feature;

use App\Models\User;
use Illuminate\Foundation\Testing\RefreshDatabase;
use Tests\TestCase;

class QuestionAdminTest extends TestCase
{
    use RefreshDatabase;

    protected function setUp(): void
    {
        parent::setUp();
        $this->assertSame('drivetest_test', config('database.connections.mysql.database'));
    }

    private function payload(): array
    {
        return ['prompt' => 'Which class contains warning signs?', 'topic' => 'classes', 'type' => 'single', 'options' => [['id' => 'a', 'label' => 'Class A'], ['id' => 'b', 'label' => 'Class B']], 'correct_ids' => ['b'], 'explanation' => 'Class B contains warning signs.', 'sign_id' => null, 'class_code' => 'B', 'subcategory_id' => null, 'group_key' => null, 'group_order' => 0, 'shuffle_options' => true, 'status' => 'draft', 'reviewed' => false, 'source_notes' => 'Draft transcription.'];
    }

    public function test_only_admins_can_access_the_editor_api(): void
    {
        $this->getJson('/api/v1/admin/questions')->assertUnauthorized();
        $this->actingAs(User::factory()->create())->getJson('/api/v1/admin/questions')->assertForbidden();
        $this->actingAs(User::factory()->create(['is_admin' => true]))->getJson('/api/v1/admin/questions')->assertOk();
    }

    public function test_editor_saves_versions_and_requires_review_before_publishing(): void
    {
        $this->actingAs(User::factory()->create(['is_admin' => true]));
        $p = $this->payload();
        $q = $this->postJson('/api/v1/admin/questions', $p)->assertCreated()->json('data');
        $this->assertDatabaseHas('questions', ['id' => $q['id'], 'status' => 'draft']);
        $p['status'] = 'published';
        $p['version'] = 1;
        $this->putJson('/api/v1/admin/questions/'.$q['id'], $p)->assertUnprocessable();
        $p['reviewed'] = true;
        $this->putJson('/api/v1/admin/questions/'.$q['id'], $p)->assertOk()->assertJsonPath('data.version', 2)->assertJsonPath('data.status', 'published');
        $this->putJson('/api/v1/admin/questions/'.$q['id'], $p)->assertConflict();
    }

    public function test_answer_keys_are_validated(): void
    {
        $this->actingAs(User::factory()->create(['is_admin' => true]));
        $p = $this->payload();
        $p['correct_ids'] = ['missing'];
        $this->postJson('/api/v1/admin/questions', $p)->assertUnprocessable();
        $p['correct_ids'] = ['a', 'b'];
        $this->postJson('/api/v1/admin/questions', $p)->assertUnprocessable();
        $this->assertDatabaseCount('questions', 0);
    }

    public function test_login_is_throttled_and_normal_users_cannot_login_as_admin(): void
    {
        $user = User::factory()->create(['password' => 'not-an-admin-password']);
        for ($i = 0; $i < 5; $i++) {
            $this->postJson('/api/v1/admin/login', ['email' => $user->email, 'password' => 'not-an-admin-password'])->assertUnprocessable();
        }
        $this->postJson('/api/v1/admin/login', ['email' => $user->email, 'password' => 'not-an-admin-password'])->assertStatus(429);
    }
}
