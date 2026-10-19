<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    public function up(): void
    {
        Schema::table('users', function (Blueprint $table): void {
            $table->boolean('is_admin')->default(false);
        });
        Schema::create('questions', function (Blueprint $table): void {
            $table->uuid('id')->primary();
            $table->unsignedInteger('version')->default(1);
            $table->text('prompt');
            $table->string('topic', 30)->index();
            $table->string('type', 10);
            $table->json('options');
            $table->json('correct_ids');
            $table->text('explanation');
            $table->string('sign_id', 120)->nullable();
            $table->foreign('sign_id')->references('id')->on('signs')->restrictOnDelete();
            $table->string('class_code', 1)->nullable();
            $table->string('subcategory_id', 40)->nullable();
            $table->string('group_key', 80)->nullable()->index();
            $table->unsignedSmallInteger('group_order')->default(0);
            $table->boolean('shuffle_options')->default(true);
            $table->string('status', 15)->default('draft')->index();
            $table->text('source_notes')->nullable();
            $table->timestamp('reviewed_at')->nullable();
            $table->timestamps();
        });
        Schema::create('quiz_attempts', function (Blueprint $table): void {
            $table->uuid('id')->primary();
            $table->string('owner_hash', 64)->index();
            $table->uuid('public_id')->unique();
            $table->string('mode', 20);
            $table->string('topic', 30);
            $table->json('filters');
            $table->json('items');
            $table->json('answers');
            $table->unsignedSmallInteger('total');
            $table->unsignedSmallInteger('score')->nullable();
            $table->string('status', 20)->default('active')->index();
            $table->timestamp('started_at');
            $table->timestamp('expires_at')->index();
            $table->timestamp('completed_at')->nullable();
            $table->timestamps();
        });
    }

    public function down(): void
    {
        Schema::dropIfExists('quiz_attempts');
        Schema::dropIfExists('questions');
        Schema::table('users', function (Blueprint $table): void {
            $table->dropColumn('is_admin');
        });
    }
};
