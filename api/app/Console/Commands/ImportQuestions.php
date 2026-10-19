<?php

namespace App\Console\Commands;

use App\Http\Requests\SaveQuestionRequest;
use App\Models\Question;
use App\Models\User;
use Illuminate\Console\Command;
use Illuminate\Support\Facades\DB;
use Illuminate\Validation\ValidationException;

class ImportQuestions extends Command
{
    protected $signature = 'questions:import {file} {--dry-run}';

    protected $description = 'Validate and import new questions as drafts; never overwrite or publish existing questions';

    public function handle(): int
    {
        $path = (string) $this->argument('file');
        if (! is_file($path) || filesize($path) > 5 * 1024 * 1024) {
            $this->error('Provide a JSON file up to 5 MB.');

            return self::FAILURE;
        }
        try {
            $rows = json_decode(file_get_contents($path), true, 512, JSON_THROW_ON_ERROR);
        } catch (\JsonException) {
            $this->error('Invalid JSON.');

            return self::FAILURE;
        }
        if (! is_array($rows) || ! array_is_list($rows) || count($rows) < 1 || count($rows) > 500) {
            $this->error('Provide a JSON array of 1–500 questions.');

            return self::FAILURE;
        }
        $validated = [];
        $prompts = [];
        $actor = new User;
        $actor->is_admin = true;
        foreach ($rows as $index => $row) {
            if (! is_array($row)) {
                $this->error('Each entry must be a question object.');

                return self::FAILURE;
            }
            $row['status'] = 'draft';
            $row['reviewed'] = false;
            $row += ['group_order' => 0, 'shuffle_options' => true];
            $request = SaveQuestionRequest::create('/', 'POST', $row);
            $request->setContainer(app())->setRedirector(app('redirect'));
            $request->setUserResolver(fn () => $actor);
            try {
                $request->validateResolved();
            } catch (ValidationException $e) {
                $this->error('Question '.($index + 1).': '.implode(' ', array_merge(...array_values($e->errors()))));

                return self::FAILURE;
            }
            $data = $request->safe()->except(['reviewed', 'version']);
            if (in_array($data['prompt'], $prompts, true) || Question::where('prompt', $data['prompt'])->exists()) {
                $this->error('Question '.($index + 1).' repeats an existing prompt. Use the editor to update existing content.');

                return self::FAILURE;
            }
            $prompts[] = $data['prompt'];
            $validated[] = $data + ['version' => 1, 'reviewed_at' => null];
        }
        if ($this->option('dry-run')) {
            $this->info(count($validated).' valid draft question(s). No changes made.');

            return self::SUCCESS;
        }
        DB::transaction(function () use ($validated): void {
            foreach ($validated as $row) {
                Question::create($row);
            }
        });
        $this->info(count($validated).' question(s) imported as drafts. Review them in /admin.');

        return self::SUCCESS;
    }
}
