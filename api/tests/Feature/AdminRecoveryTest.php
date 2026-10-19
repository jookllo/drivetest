<?php

namespace Tests\Feature;

use App\Models\User;
use Illuminate\Foundation\Testing\RefreshDatabase;
use Illuminate\Support\Facades\DB;
use Illuminate\Support\Facades\Hash;
use Tests\TestCase;

class AdminRecoveryTest extends TestCase
{
    use RefreshDatabase;

    public function test_editor_has_the_requested_address(): void
    {
        $this->get('/mdosimimi')->assertOk();
        $this->get('/admin')->assertNotFound();
        $this->getJson('/api/v1/admin/questions')->assertUnauthorized();
    }

    public function test_terminal_recovery_changes_password_and_revokes_database_sessions(): void
    {
        config(['session.driver' => 'database']);
        $admin = User::factory()->create(['is_admin' => true]);
        DB::table('sessions')->insert(['id' => 'old-admin-session', 'user_id' => $admin->id, 'payload' => '', 'last_activity' => time()]);
        $this->artisan('app:reset-admin-password', ['email' => $admin->email])
            ->expectsQuestion('New password (at least 12 characters)', 'a-new-test-password')
            ->expectsQuestion('Confirm password', 'a-new-test-password')->assertSuccessful();
        $this->assertTrue(Hash::check('a-new-test-password', $admin->fresh()->password));
        $this->assertDatabaseMissing('sessions', ['id' => 'old-admin-session']);
    }

    public function test_recovery_rejects_non_admins_and_mismatched_passwords(): void
    {
        $user = User::factory()->create();
        $this->artisan('app:reset-admin-password', ['email' => $user->email])->assertFailed();
        $admin = User::factory()->create(['is_admin' => true]);
        $hash = $admin->password;
        $this->artisan('app:reset-admin-password', ['email' => $admin->email])
            ->expectsQuestion('New password (at least 12 characters)', 'a-new-test-password')
            ->expectsQuestion('Confirm password', 'a-different-password')->assertFailed();
        $this->assertSame($hash, $admin->fresh()->password);
    }
}
