<?php

use App\Http\Controllers\Api\SignController;
use App\Http\Middleware\LocalSignPreview;
use Illuminate\Support\Facades\Route;

Route::prefix('v1')->middleware('throttle:catalog')->group(function (): void {
    Route::get('classes', [SignController::class, 'classes'])->name('api.classes');
    Route::get('signs', [SignController::class, 'index'])->name('api.signs.index');
    Route::get('signs/{id}/image', [SignController::class, 'image'])->name('api.signs.image');
    Route::get('signs/{id}', [SignController::class, 'show'])->name('api.signs.show');
});

Route::prefix('v1/preview')->middleware(LocalSignPreview::class)->group(function (): void {
    Route::get('signs', [SignController::class, 'index'])->name('api.preview.signs.index');
    Route::get('signs/{id}/image', [SignController::class, 'image'])->name('api.preview.signs.image');
    Route::get('signs/{id}', [SignController::class, 'show'])->name('api.preview.signs.show');
});
