<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{{ $result->score }}/{{ $result->total }} on DriveTest</title>
<meta property="og:title" content="{{ $result->score }}/{{ $result->total }} on DriveTest">
<meta property="og:description" content="A road-sign practice result. Try a quiz without an account.">
<meta property="og:type" content="website"><meta property="og:url" content="{{ route('quiz.result', ['publicId'=>$result->public_id]) }}">
<meta property="og:image" content="{{ asset('assets/mascot/drivetest-results-blanket-v1.png') }}">
<link rel="stylesheet" href="{{ asset('assets/quiz/quiz.css') }}"></head><body>
<header class="site-header"><div class="site-header__inner"><a class="brand" href="{{ route('quiz') }}">DriveTest</a></div></header>
<main class="wrap"><p class="eyebrow">Shared practice score</p><h1>A little practice goes a long way.</h1><div class="card result-hero"><div class="result-mascot"><img src="{{ asset('assets/mascot/drivetest-results-blanket-v1.png') }}" width="1306" height="1205" alt=""></div><div><p class="score-line"><strong class="score-big">{{ $result->score }}</strong><span class="score-of">/ {{ $result->total }}</span></p><p>{{ config('quiz.topics.'.$result->topic, 'Mixed practice') }} · {{ $result->mode === 'challenge' ? 'Timed challenge' : 'Untimed practice' }}</p><a class="btn btn--primary" href="{{ route('quiz') }}">Try a quiz</a></div></div><p class="result-topic">This is a practice score, not a driving qualification.</p></main>
</body></html>
