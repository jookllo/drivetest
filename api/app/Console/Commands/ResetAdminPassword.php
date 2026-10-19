<?php

namespace App\Console\Commands;

use App\Models\User;
use Illuminate\Console\Command;
use Illuminate\Support\Facades\DB;
use Illuminate\Support\Str;

class ResetAdminPassword extends Command
{
    protected $signature = 'app:reset-admin-password {email}';

    protected $description = 'Reset an existing administrator password privately from the server terminal';

    public function handle(): int
    {
        $user = User::where('email', $this->argument('email'))->where('is_admin', true)->first();
        if (! $user) {
            $this->error('No administrator exists with that email address.');

            return self::FAILURE;
        }
        $password = $this->secret('New password (at least 12 characters)');
        if (! is_string($password) || strlen($password) < 12 || $password !== $this->secret('Confirm password')) {
            $this->error('Passwords must match and contain at least 12 characters.');

            return self::FAILURE;
        }
        DB::transaction(function () use ($user, $password): void {
            $user->password = $password;
            $user->remember_token = Str::random(60);
            $user->save();
            if (config('session.driver') === 'database') {
                DB::connection(config('session.connection'))->table(config('session.table', 'sessions'))->where('user_id', $user->id)->delete();
            }
        });
        $this->info('Password reset. Sign in at /mdosimimi with your new password.');

        return self::SUCCESS;
    }
}
