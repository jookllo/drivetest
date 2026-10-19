<?php

use Illuminate\Support\Facades\Route;

Route::view('/', 'quiz')->name('quiz');
Route::view('/quiz', 'quiz');

require __DIR__.'/quiz.php';
