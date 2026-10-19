<?php

namespace App\Console\Commands;

use Illuminate\Console\Command;
use Symfony\Component\Process\Process;

class SetupMySql extends Command
{
    protected $signature = 'app:setup-mysql';

    protected $description = 'Create a new local drivetest MySQL database and restricted application user';

    public function handle(): int
    {
        if (! app()->environment('local')) {
            $this->error('This setup command is only for local development.');

            return self::FAILURE;
        }
        $path = base_path('.env');
        if (! is_writable($path)) {
            $this->error('A writable local .env file is required.');

            return self::FAILURE;
        }
        $check = new Process(['sudo', '-n', 'mysql', '--batch', '--skip-column-names']);
        $check->setInput("SELECT (SELECT COUNT(*) FROM information_schema.SCHEMATA WHERE SCHEMA_NAME='drivetest') + (SELECT COUNT(*) FROM mysql.user WHERE User='drivetest_app');");
        $check->run();
        if (! $check->isSuccessful()) {
            $this->error('Run sudo -v in your own terminal, then rerun php artisan app:setup-mysql there.');

            return self::FAILURE;
        }
        if (trim($check->getOutput()) !== '0') {
            $this->error('The database or user already exists. Nothing changed; configure .env with existing credentials.');

            return self::FAILURE;
        }
        $password = bin2hex(random_bytes(24));
        $setup = new Process(['sudo', '-n', 'mysql']);
        $setup->setInput("CREATE DATABASE drivetest CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci; CREATE USER 'drivetest_app'@'127.0.0.1' IDENTIFIED BY '{$password}'; GRANT ALL PRIVILEGES ON drivetest.* TO 'drivetest_app'@'127.0.0.1';");
        $setup->run();
        if (! $setup->isSuccessful()) {
            $this->error('Database setup failed; check the local MySQL administrator configuration before retrying.');

            return self::FAILURE;
        }
        $env = file_get_contents($path);
        foreach (['DB_CONNECTION' => 'mysql', 'DB_HOST' => '127.0.0.1', 'DB_PORT' => '3306', 'DB_DATABASE' => 'drivetest', 'DB_USERNAME' => 'drivetest_app', 'DB_PASSWORD' => $password] as $key => $value) {
            $env = preg_replace('/^'.preg_quote($key, '/').'=.*/m', $key.'='.$value, $env);
        }
        if (file_put_contents($path, $env, LOCK_EX) === false) {
            $this->error('Database created but .env could not be saved. Reset the application user password locally.');

            return self::FAILURE;
        }
        chmod($path, 0600);
        $this->call('config:clear');
        $this->info('Database and application user created. Credentials saved privately in .env. Run php artisan migrate next.');

        return self::SUCCESS;
    }
}
