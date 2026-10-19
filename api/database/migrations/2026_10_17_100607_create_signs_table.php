<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\DB;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    public function up(): void
    {
        Schema::create('sign_classes', function (Blueprint $table): void {
            $table->string('code', 1)->primary();
            $table->string('name');
        });
        Schema::create('sign_subcategories', function (Blueprint $table): void {
            $table->string('id', 40)->primary();
            $table->string('class_code', 1);
            $table->string('name');
            $table->foreign('class_code')->references('code')->on('sign_classes');
            $table->unique(['id', 'class_code']);
        });
        $classes = [
            'A' => ['Regulatory signs', ['priority' => 'Priority signs', 'prohibitory' => 'Prohibitory signs', 'compulsory' => 'Compulsory signs']],
            'B' => ['Warning signs', []],
            'C' => ['Informatory signs', ['advance-directional' => 'Advance directional signs', 'route-confirmatory' => 'Route confirmatory signs', 'facility' => 'Facility signs']],
        ];
        foreach ($classes as $code => [$name, $subcategories]) {
            DB::table('sign_classes')->insert(compact('code', 'name'));
            foreach ($subcategories as $id => $subcategory) {
                DB::table('sign_subcategories')->insert(['id' => $id, 'class_code' => $code, 'name' => $subcategory]);
            }
        }
        Schema::create('signs', function (Blueprint $table): void {
            $table->string('id', 120)->primary();
            $table->string('name');
            $table->string('class_code', 1)->nullable();
            $table->string('subcategory_id', 40)->nullable();
            $table->text('meaning')->nullable();
            $table->string('image_path')->nullable();
            $table->enum('status', ['draft', 'published'])->default('draft')->index();
            $table->text('review_notes')->nullable();
            $table->timestamps();
            $table->foreign('class_code')->references('code')->on('sign_classes');
            $table->foreign(['subcategory_id', 'class_code'])->references(['id', 'class_code'])->on('sign_subcategories');
        });
    }

    public function down(): void
    {
        Schema::dropIfExists('signs');
        Schema::dropIfExists('sign_subcategories');
        Schema::dropIfExists('sign_classes');
    }
};
