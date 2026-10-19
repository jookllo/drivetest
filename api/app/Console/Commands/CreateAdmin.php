<?php

namespace App\Console\Commands;

use App\Models\User;
use Illuminate\Console\Command;
use Illuminate\Support\Facades\Validator;

class CreateAdmin extends Command
{
    protected $signature = 'app:create-admin {email} {--name=Administrator}';

    protected $description = 'Create a new administrator with a password entered privately in the terminal';

    public function handle(): int
    {
        $email = (string) $this->argument('email');
        if (Validator::make(['email' => $email], ['email' => 'required|email|max:255'])->fails() || User::where('email', $email)->exists()) {
            $this->error('Provide a valid unused email address.');

            return self::FAILURE;
        }
        $password = $this->secret('Choose an admin password (at least 12 characters)');
        if (! is_string($password) || strlen($password) < 12 || $password !== $this->secret('Confirm password')) {
            $this->error('Passwords must match and contain at least 12 characters.');

            return self::FAILURE;
        }
        $user = new User(['name' => (string) $this->option('name'), 'email' => $email, 'password' => $password]);
        $user->is_admin = true;
        $user->save();
        $this->info('Administrator created. Sign in at /mdosimimi.');

        return self::SUCCESS;
    }
}
