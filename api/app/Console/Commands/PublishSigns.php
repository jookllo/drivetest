<?php

namespace App\Console\Commands;

use App\Models\Sign;
use Illuminate\Console\Command;

class PublishSigns extends Command
{
    protected $signature = 'signs:publish
        {--all : Change every matching sign}
        {--class= : Limit to one class code (A, B, or C)}
        {--id=* : Limit to specific sign IDs}
        {--unpublish : Move matched signs back to draft instead of publishing}
        {--dry-run : Show what would change without changing anything}
        {--force : Skip the confirmation prompt}';

    protected $description = 'Publish reviewed signs (or unpublish them) so the public API and quiz can show them';

    public function handle(): int
    {
        $target = $this->option('unpublish') ? 'draft' : 'published';
        $verb = $target === 'published' ? 'publish' : 'unpublish';
        $query = Sign::query()->where('status', '!=', $target);

        $all = (bool) $this->option('all');
        $class = $this->option('class');
        $ids = array_values(array_filter((array) $this->option('id')));

        $selected = array_filter([$all, $class !== null, $ids !== []]);
        if (count($selected) !== 1) {
            $this->error('Choose exactly one selector: --all, --class=CODE, or --id=ID (repeatable).');

            return self::FAILURE;
        }

        if ($class !== null) {
            $class = strtoupper((string) $class);
            if (! in_array($class, ['A', 'B', 'C'], true)) {
                $this->error('Unknown class code. Use A, B, or C.');

                return self::FAILURE;
            }
            $query->where('class_code', $class);
        }

        if ($ids !== []) {
            $query->whereIn('id', $ids);
            $missing = array_diff($ids, Sign::query()->whereIn('id', $ids)->pluck('id')->all());
            if ($missing !== []) {
                $this->warn('Unknown sign IDs ignored: '.implode(', ', $missing));
            }
        }

        $signs = $query->orderBy('id')->get(['id', 'name', 'class_code', 'status']);

        if ($signs->isEmpty()) {
            $this->info('No matching draft signs.');

            return self::SUCCESS;
        }

        $pending = $signs->filter(fn (Sign $sign): bool => $sign->status !== $target)->count();

        $this->table(
            ['Class', 'Count'],
            $signs->groupBy(fn (Sign $sign): string => $sign->class_code ?? 'Unassigned')
                ->map(fn ($group, string $code): array => [$code, $group->count()])
                ->values()
                ->all()
        );
        $this->info($pending.' sign(s) would be marked as '.$target.'.');

        if ($this->option('dry-run')) {
            $this->comment('Dry run: nothing was changed.');

            return self::SUCCESS;
        }

        if (! $this->option('force') && ! $this->confirm(ucfirst($verb).' these '.$pending.' sign(s)?')) {
            $this->comment('Cancelled.');

            return self::SUCCESS;
        }

        $updated = Sign::query()
            ->whereIn('id', $signs->pluck('id'))
            ->where('status', '!=', $target)
            ->update(['status' => $target, 'updated_at' => now()]);

        $this->info($updated.' sign(s) marked as '.$target.'.');

        return self::SUCCESS;
    }
}
