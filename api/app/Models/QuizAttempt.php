<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Concerns\HasUuids;
use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Database\Eloquent\Model;

class QuizAttempt extends Model
{
    use HasFactory, HasUuids;

    protected $guarded = ['id'];

    protected $hidden = ['owner_hash', 'items', 'answers'];

    protected function casts(): array
    {
        return ['filters' => 'array', 'items' => 'array', 'answers' => 'array', 'started_at' => 'immutable_datetime', 'expires_at' => 'immutable_datetime', 'completed_at' => 'immutable_datetime', 'total' => 'integer', 'score' => 'integer'];
    }
}
