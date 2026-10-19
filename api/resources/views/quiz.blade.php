<!DOCTYPE html>
<html lang="{{ str_replace('_', '-', app()->getLocale()) }}">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>DriveTest — road sign practice</title>
    <meta name="description" content="Free, no-account practice quizzes for road signs: names, meanings, classes, and subcategories.">
    <link rel="stylesheet" href="{{ asset('assets/quiz/quiz.css') }}">
</head>
<body>
    @php
        $demoAvailable = app()->environment('local') && in_array(request()->ip(), ['127.0.0.1', '::1'], true);
        $demo = $demoAvailable && request()->boolean('demo');
    @endphp
    <div id="quiz-app" data-demo-available="{{ $demoAvailable ? 'true' : 'false' }}"></div>
    @if ($demo)
        <script id="quiz-demo-data" type="application/json">{!! json_encode(json_decode(file_get_contents(resource_path('quiz-demo.json')), true, 512, JSON_THROW_ON_ERROR), JSON_HEX_TAG | JSON_HEX_AMP | JSON_HEX_APOS | JSON_HEX_QUOT | JSON_THROW_ON_ERROR) !!}</script>
    @endif
    <script src="{{ asset('vendor/vue.global.prod.js') }}"></script>
    <script src="{{ asset($demo ? 'assets/quiz/demo.js' : 'assets/quiz/app.js') }}?v={{ filemtime(public_path($demo ? 'assets/quiz/demo.js' : 'assets/quiz/app.js')) }}"></script>
</body>
</html>
