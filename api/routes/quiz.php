<?php

use App\Http\Controllers\AdminAuthController;
use App\Http\Controllers\Api\QuestionAdminController;
use App\Http\Controllers\Api\QuizController;
use App\Http\Middleware\PrivateQuizResponse;
use App\Http\Middleware\RequireAdmin;
use App\Models\QuizAttempt;
use Illuminate\Support\Facades\Route;

Route::view('/mdosimimi', 'admin')->middleware(PrivateQuizResponse::class)->name('admin');
Route::get('/results/{publicId}', function (string $publicId) {
    $result = QuizAttempt::where('public_id', $publicId)->where('status', '!=', 'active')->firstOrFail();

    return view('result', ['result' => $result]);
})->middleware('throttle:catalog')->name('quiz.result');
Route::prefix('api/v1')->middleware([PrivateQuizResponse::class, 'throttle:quiz'])->group(function (): void {
    Route::get('quiz-session', [QuizController::class, 'session']);
    Route::get('quiz-topics', [QuizController::class, 'topics']);
    Route::post('quiz-attempts', [QuizController::class, 'store'])->middleware('throttle:quiz-start')->block();
    Route::get('quiz-attempts/{id}', [QuizController::class, 'show']);
    Route::post('quiz-attempts/{id}/answers', [QuizController::class, 'answer']);
    Route::post('quiz-attempts/{id}/complete', [QuizController::class, 'complete']);
    Route::get('results/{publicId}', [QuizController::class, 'result']);
    Route::get('admin/session', [AdminAuthController::class, 'session']);
    Route::post('admin/login', [AdminAuthController::class, 'login'])->middleware('throttle:admin-login')->block();
    Route::post('admin/logout', [AdminAuthController::class, 'logout'])->block();
    Route::prefix('admin')->middleware([RequireAdmin::class, 'auth.session'])->group(function (): void {
        Route::get('questions', [QuestionAdminController::class, 'index']);
        Route::post('questions', [QuestionAdminController::class, 'save']);
        Route::put('questions/{id}', [QuestionAdminController::class, 'save']);
        Route::get('signs', [QuestionAdminController::class, 'signs']);
        Route::put('signs/{id}', [QuestionAdminController::class, 'sign']);
        Route::get('signs/{id}/image', [QuestionAdminController::class, 'image']);
    });
});
