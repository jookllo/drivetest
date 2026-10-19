<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Concerns\HasUuids;
use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\BelongsTo;

class Question extends Model
{
    use HasFactory, HasUuids;

    protected $guarded = ['id'];

    protected function casts(): array
    {
        return ['options' => 'array', 'correct_ids' => 'array', 'shuffle_options' => 'boolean', 'reviewed_at' => 'datetime', 'version' => 'integer', 'group_order' => 'integer'];
    }

    public function sign(): BelongsTo
    {
        return $this->belongsTo(Sign::class);
    }
}
