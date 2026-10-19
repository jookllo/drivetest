<?php

namespace Database\Seeders;

use App\Models\Question;
use Illuminate\Database\Seeder;

class StarterQuestionSeeder extends Seeder
{
    public function run(): void
    {
        $items = [
            ['Which class contains warning signs?', 'classes', ['Class A — Regulatory', 'Class B — Warning', 'Class C — Informatory'], [1], 'Warning signs belong to Class B.', 'B', null],
            ['Which class contains regulatory signs?', 'classes', ['Class A — Regulatory', 'Class B — Warning', 'Class C — Informatory'], [0], 'Regulatory signs belong to Class A.', 'A', null],
            ['Which class contains informatory signs?', 'classes', ['Class A — Regulatory', 'Class B — Warning', 'Class C — Informatory'], [2], 'Informatory signs belong to Class C.', 'C', null],
            ['Which subcategory contains Stop and Give way?', 'subcategories', ['Priority', 'Prohibitory', 'Compulsory'], [0], 'Stop and Give way are priority signs.', 'A', 'priority'],
            ['Which Class A subcategory gives compulsory instructions?', 'subcategories', ['Priority', 'Prohibitory', 'Compulsory'], [2], 'Compulsory is a regulatory subcategory.', 'A', 'compulsory'],
            ['Which Class A subcategory describes prohibitions?', 'subcategories', ['Priority', 'Prohibitory', 'Compulsory'], [1], 'Prohibitory signs indicate restrictions.', 'A', 'prohibitory'],
            ['Which of these are regulatory subcategories?', 'general', ['Priority', 'Facility', 'Compulsory', 'Prohibitory'], [0, 2, 3], 'Class A contains priority, prohibitory and compulsory signs.', null, null],
            ['Which of these are informatory subcategories?', 'general', ['Advance directional', 'Route confirmatory', 'Facility', 'Priority'], [0, 1, 2], 'Class C includes advance directional, route confirmatory and facility signs.', null, null],
            ['Which class would you study for warning signs?', 'general', ['A', 'B', 'C'], [1], 'Class B contains warning signs.', null, null],
            ['Which pair contains priority signs?', 'general', ['Stop and Give way', 'Hospital and Fuel station', 'Bend and Junction'], [0], 'Stop and Give way belong to priority signs.', null, null],
        ];
        foreach ($items as [$prompt,$topic,$labels,$correct,$explanation,$class,$subcategory]) {
            Question::firstOrCreate(['prompt' => $prompt], ['topic' => $topic, 'type' => count($correct) > 1 ? 'multi' : 'single',
                'options' => array_map(fn ($label, $i) => ['id' => 'o'.$i, 'label' => $label], $labels, array_keys($labels)),
                'correct_ids' => array_map(fn ($i) => 'o'.$i, $correct), 'explanation' => $explanation, 'class_code' => $class, 'subcategory_id' => $subcategory,
                'status' => 'draft', 'source_notes' => 'Starter draft based on the project taxonomy. Owner review required before publication.', 'shuffle_options' => true, 'group_order' => 0]);
        }
    }
}
