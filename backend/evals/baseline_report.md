# Nagham AI eval run — `baseline`

- Total cases: 44
- Overall pass rate: 46%
- Latency: mean 2.806s, p50 2.52s, p95 6.24s

## By category

| Category | Passed | Total | Rate |
|---|---|---|---|
| ambiguous_request | 1 | 1 | 100% |
| artist_spelling_variant | 1 | 4 | 25% |
| colloquial_query | 1 | 1 | 100% |
| contradiction | 1 | 1 | 100% |
| empty_result | 2 | 2 | 100% |
| follow_up | 0 | 3 | 0% |
| hallucination_resistance | 3 | 3 | 100% |
| hybrid_search | 1 | 3 | 33% |
| maqam_spelling_variant | 1 | 3 | 33% |
| multi_constraint | 1 | 2 | 50% |
| music_theory | 0 | 4 | 0% |
| negation | 0 | 2 | 0% |
| result_count | 2 | 2 | 100% |
| semantic_search | 2 | 4 | 50% |
| song_specific_question | 0 | 1 | 0% |
| structured_search | 4 | 8 | 50% |

## Failing cases

### `struct-artist-01` (structured_search)
- [FAIL] input: 'اعطيني اغاني فيروز'
  - failed checks: {'exact_song_set': False}
  - found_ids: []

### `struct-maqam-01` (structured_search)
- [FAIL] input: 'اعطيني اغاني على مقام الحجاز'
  - failed checks: {'exact_song_set': False}
  - found_ids: []

### `struct-difficulty-01` (structured_search)
- [FAIL] input: 'اعطيني اغاني سهلة'
  - failed checks: {'exact_song_set': False}
  - found_ids: []

### `struct-combo-02` (structured_search)
- [FAIL] input: 'أغنية لمحمد عبد الوهاب على مقام الراست'
  - failed checks: {'exact_song_set': False}
  - found_ids: []

### `spelling-hamza-01` (artist_spelling_variant)
- [FAIL] input: 'اعطيني اغاني ام كلثوم'
  - failed checks: {'subset_and_nonempty': False}
  - found_ids: []

### `spelling-hamza-02` (artist_spelling_variant)
- [FAIL] input: 'اغاني لإم كلثوم'
  - failed checks: {'subset_and_nonempty': False}
  - found_ids: []

### `spelling-diacritics-01` (artist_spelling_variant)
- [FAIL] input: 'أَغَانِي فَيْرُوز'
  - failed checks: {'exact_song_set': False}
  - found_ids: []

### `spelling-maqam-variant-02` (maqam_spelling_variant)
- [FAIL] input: 'اعطيني اغاني على نهوند'
  - failed checks: {'exact_song_set': False}
  - found_ids: []

### `spelling-maqam-variant-03` (maqam_spelling_variant)
- [FAIL] input: 'عندك اغاني على مقام الراصت'
  - failed checks: {'subset_and_nonempty': False}
  - found_ids: []

### `semantic-topic-01` (semantic_search)
- [FAIL] input: 'بدي اغنية عن السفر'
  - failed checks: {'top1_match': False}
  - found_ids: []

### `semantic-mood-02` (semantic_search)
- [FAIL] input: 'اغاني هادئة ورومانسية'
  - failed checks: {'subset_and_nonempty': False}
  - found_ids: [134, 136, 139, 133, 130, 127, 143, 141, 135, 144]

### `hybrid-02` (hybrid_search)
- [FAIL] input: 'اغنية عن العودة لفيروز على مقام عجم'
  - failed checks: {'exact_song_set': False}
  - found_ids: []

### `hybrid-03` (hybrid_search)
- [FAIL] input: 'اغنية عن الحب والوفاء على مقام الراست'
  - failed checks: {'top1_match': False}
  - found_ids: []

### `multiconstraint-01` (multi_constraint)
- [FAIL] input: 'اعطيني اغاني لفيروز أو أم كلثوم'
  - failed checks: {'subset_and_nonempty': False}
  - found_ids: []

### `negation-01` (negation)
- [FAIL] input: 'اعطيني اغاني عن الحب بس مش لأم كلثوم'
  - failed checks: {'artist_excluded': False}
  - found_ids: [136, 130, 141, 139, 134]

### `negation-02` (negation)
- [FAIL] input: 'أغاني على مقام الحجاز لكن ليس لصباح فخري'
  - failed checks: {'exact_song_set': False}
  - found_ids: []

### `theory-01` (music_theory)
- [FAIL] input: 'شو الفرق بين الصبا والبياتي؟'
  - failed checks: {'intent_match': False}
  - found_ids: []

### `theory-02` (music_theory)
- [FAIL] input: 'شو هو جنس الحجاز؟'
  - failed checks: {'intent_match': False}
  - found_ids: []

### `theory-03` (music_theory)
- [FAIL] input: 'اشرحلي سلم مقام الراست'
  - failed checks: {'intent_match': False}
  - found_ids: []

### `theory-04` (music_theory)
- [FAIL] input: 'ما هو غماز مقام الصبا؟'
  - failed checks: {'intent_match': False}
  - found_ids: []

### `song-question-01` (song_specific_question)
- [FAIL] input: 'شو مقام اغنية حنين إلى الوطن؟'
  - failed checks: {'exact_song_set': False, 'intent_match': False}
  - found_ids: [144, 126, 132]

### `followup-01` (follow_up)
- [FAIL] input: 'اعطيني اغاني على مقام الراست'
  - failed checks: {'exact_song_set': False}
  - found_ids: []
- [FAIL] input: 'من هالاغاني، اختار الأسهل'
  - failed checks: {'subset_and_nonempty': False, 'intent_match': False}
  - found_ids: []

### `followup-02` (follow_up)
- [FAIL] input: 'اعطيني اغنية لفيروز على مقام نهاوند'
  - failed checks: {'exact_song_set': False}
  - found_ids: []
- [FAIL] input: 'طيب اقترح علي اغنية بعدها تكون بنفس المقام'
  - failed checks: {'subset_and_nonempty': False, 'intent_match': False}
  - found_ids: [131, 133, 135, 142, 139, 143]

### `followup-03` (follow_up)
- [PASS] input: 'اعطيني اغاني حزينة لعبد الحليم حافظ'
  - found_ids: [141]
- [FAIL] input: 'و شو مقام اول اغنية منهم؟'
  - failed checks: {'intent_match': False}
  - found_ids: [126, 128, 129]
