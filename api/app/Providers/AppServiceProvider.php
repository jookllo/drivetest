<?php

namespace App\Providers;

use Illuminate\Cache\RateLimiting\Limit;
use Illuminate\Support\Facades\RateLimiter;
use Illuminate\Support\ServiceProvider;

class AppServiceProvider extends ServiceProvider
{
    /**
     * Register any application services.
     */
    public function register(): void
    {
        //
    }

    /**
     * Bootstrap any application services.
     */
    public function boot(): void
    {
        RateLimiter::for('catalog', fn ($request) => Limit::perMinute(300)->by($request->ip()));
        RateLimiter::for('quiz', fn ($request) => Limit::perMinute(180)->by($request->ip()));
        RateLimiter::for('quiz-start', fn ($request) => Limit::perMinute(10)->by($request->ip()));
        RateLimiter::for('admin-login', fn ($request) => Limit::perMinute(5)->by($request->ip()));
    }
}
