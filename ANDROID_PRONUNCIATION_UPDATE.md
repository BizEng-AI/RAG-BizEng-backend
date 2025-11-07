# 🎤 ENHANCED PRONUNCIATION ASSESSMENT - Android Integration Guide

**Server Updated:** October 25, 2025  
**Changes:** Phoneme-level analysis, detailed feedback, pronunciation tips, **IPA transcription**

---

## 📋 WHAT CHANGED ON SERVER

### ✅ New Features Added:
1. **Phoneme-level scoring** - See which specific sounds are mispronounced
2. **IPA (International Phonetic Alphabet) transcription** - Full phonetic notation for each word ⭐ NEW
3. **Detailed feedback per word** - Specific tips for each mispronounced word
4. **Phonetic pronunciation tips** - How to correctly produce each sound
5. **More accurate scoring** - Better granularity (6 levels instead of 3)

---

## 🔄 UPDATED API RESPONSE FORMAT

### `/pronunciation/assess` Endpoint

**Request:** (No changes - still the same)
```
POST /pronunciation/assess
Content-Type: multipart/form-data

audio: <WAV file>
reference_text: "Good morning, I would like to schedule a meeting"
```

**Response:** (ENHANCED with new fields)
```json
{
  "transcript": "Good morning I would like to schedule a meeting",
  "accuracy_score": 85.5,
  "fluency_score": 78.2,
  "completeness_score": 95.0,
  "pronunciation_score": 82.3,
  
  "feedback": "Good pronunciation! A few minor areas to improve. 👍\n📍 Words to practice: 'morning', 'schedule'\n⏱️ Fluency tip: Good pace, but try to sound more natural with fewer hesitations.",
  
  "detailed_feedback": [
    "Work on 'morning' - Focus on /ɔː/ sound: Long 'aw' sound as in 'law'. Round your lips more.",
    "Work on 'schedule' - Listen to the correct pronunciation and repeat slowly. - Break it into syllables and practice each part.",
    "Practice reading the sentence out loud several times to build muscle memory."
  ],
  
  "words": [
    {
      "word": "Good",
      "accuracy_score": 95.0,
      "error_type": null,
      "feedback": null,
      "ipa_expected": "ɡʊd",
      "ipa_actual": null,
      "phonemes": [
        {
          "phoneme": "ɡ",
          "score": 98.0
        },
        {
          "phoneme": "ʊ",
          "score": 92.0
        },
        {
          "phoneme": "d",
          "score": 96.0
        }
      ]
    },
    {
      "word": "morning",
      "accuracy_score": 55.0,
      "error_type": "Mispronunciation",
      "feedback": "Work on 'morning' - Focus on /ɔː/ sound: Long 'aw' sound as in 'law'. Round your lips more.",
      "ipa_expected": "ˈmɔːnɪŋ",
      "ipa_actual": null,
      "phonemes": [
        {
          "phoneme": "m",
          "score": 88.0
        },
        {
          "phoneme": "ɔː",
          "score": 45.0
        },
        {
          "phoneme": "n",
          "score": 82.0
        },
        {
          "phoneme": "ɪ",
          "score": 65.0
        },
        {
          "phoneme": "ŋ",
          "score": 70.0
        }
      ]
    },
    {
      "word": "schedule",
      "accuracy_score": 68.0,
      "error_type": null,
      "feedback": "Work on 'schedule' - Listen to the correct pronunciation and repeat slowly.",
      "ipa_expected": "ˈʃedjuːl",
      "ipa_actual": null,
      "phonemes": [...]
    }
  ]
}
```

---

## 📱 ANDROID DTO UPDATES

### 1. Add New Models

**File:** `app/src/main/java/com/example/myapplication/data/remote/dto/PronunciationDto.kt`

```kotlin
package com.example.myapplication.data.remote.dto

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

// NEW: Phoneme-level details
@Serializable
data class PronunciationPhonemeDto(
    val phoneme: String,              // IPA symbol: "ɔː", "θ", "ɪ", etc.
    val score: Float                  // 0-100
)

// UPDATED: Enhanced word details
@Serializable
data class PronunciationWordDto(
    val word: String,
    @SerialName("accuracy_score") val accuracyScore: Float,
    @SerialName("error_type") val errorType: String? = null,
    val feedback: String? = null,                              // NEW
    val phonemes: List<PronunciationPhonemeDto>? = null,      // NEW
    @SerialName("ipa_expected") val ipaExpected: String? = null,   // NEW ⭐ Full IPA transcription
    @SerialName("ipa_actual") val ipaActual: String? = null        // NEW (future use)
)

// UPDATED: Enhanced pronunciation result
@Serializable
data class PronunciationResultDto(
    val transcript: String,
    @SerialName("accuracy_score") val accuracyScore: Float,
    @SerialName("fluency_score") val fluencyScore: Float,
    @SerialName("completeness_score") val completenessScore: Float,
    @SerialName("pronunciation_score") val pronunciationScore: Float,
    val words: List<PronunciationWordDto>,
    val feedback: String,
    @SerialName("detailed_feedback") val detailedFeedback: List<String>? = null  // NEW
)
```

---

## 🎨 UI CHANGES NEEDED

### 1. Update Pronunciation Result Screen

**File:** `app/src/main/java/com/example/myapplication/ui/pronunciation/PronunciationResultScreen.kt`

#### Changes to Make:

1. **Show IPA transcription for each word** ⭐
   - Display the full phonetic spelling
   - Use proper font for IPA symbols

2. **Show detailed feedback section**
   - Display `detailedFeedback` list as bullet points
   - Each tip on a separate card/row

3. **Add word-by-word breakdown**
   - Expandable list showing each word
   - Show word's accuracy score
   - Display phonemes with color coding (red = bad, yellow = okay, green = good)

4. **Improved feedback display**
   - Main feedback at the top (already exists)
   - Collapsible "Detailed Tips" section below
   - Phonetic symbols rendered properly (use Unicode support)

#### Example UI Layout:

```
┌─────────────────────────────────────────┐
│ Overall Score: 82.3/100                 │
│ Good pronunciation! 👍                   │
├─────────────────────────────────────────┤
│ 📊 Breakdown:                           │
│   Accuracy:    85.5/100  ████████░      │
│   Fluency:     78.2/100  ███████▒░      │
│   Completeness: 95.0/100 █████████░     │
├─────────────────────────────────────────┤
│ 📍 Words to Practice:                   │
│                                         │
│ ❌ morning (55/100)                     │
│    IPA: /ˈmɔːnɪŋ/               ⭐ NEW │
│    /ɔː/ sound (45/100) - Focus needed  │
│    Tip: Round your lips more            │
│                                         │
│ ⚠️ schedule (68/100)                    │
│    IPA: /ˈʃedjuːl/              ⭐ NEW │
│    Break into syllables: sche-dule      │
├─────────────────────────────────────────┤
│ 💡 Detailed Tips (3)                ▼  │
│   • Work on 'morning' - Focus on /ɔː/   │
│     sound: Long 'aw' as in 'law'...     │
│   • Work on 'schedule' - Listen to...   │
│   • Practice reading the sentence...    │
└─────────────────────────────────────────┘
```

---

## 🔧 CODE EXAMPLES FOR ANDROID

### 1. Display Phoneme Breakdown WITH IPA Transcription

```kotlin
@Composable
fun PhonemeBreakdownItem(word: PronunciationWordDto) {
    Card(
        modifier = Modifier
            .fillMaxWidth()
            .padding(vertical = 4.dp)
    ) {
        Column(modifier = Modifier.padding(16.dp)) {
            // Word header
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween
            ) {
                Column {
                    Text(
                        text = word.word,
                        style = MaterialTheme.typography.titleMedium,
                        fontWeight = FontWeight.Bold
                    )
                    
                    // ⭐ NEW: Show IPA transcription
                    word.ipaExpected?.let { ipa ->
                        Text(
                            text = "IPA: /$ipa/",
                            style = MaterialTheme.typography.bodySmall,
                            color = MaterialTheme.colorScheme.primary,
                            fontFamily = NotoSansFont  // Important for proper rendering
                        )
                    }
                }
                
                // Score badge
                val color = when {
                    word.accuracyScore >= 80 -> Color.Green
                    word.accuracyScore >= 60 -> Color(0xFFFF9800) // Orange
                    else -> Color.Red
                }
                Text(
                    text = "${word.accuracyScore.toInt()}/100",
                    color = color,
                    fontWeight = FontWeight.Bold
                )
            }
            
            // Error type badge
            if (word.errorType != null) {
                Spacer(modifier = Modifier.height(4.dp))
                Text(
                    text = "⚠️ ${word.errorType}",
                    style = MaterialTheme.typography.bodySmall,
                    color = Color.Red
                )
            }
            
            // Phoneme breakdown
            word.phonemes?.let { phonemes ->
                Spacer(modifier = Modifier.height(8.dp))
                Text(
                    text = "Phonemes:",
                    style = MaterialTheme.typography.bodySmall,
                    fontWeight = FontWeight.SemiBold
                )
                
                FlowRow(
                    modifier = Modifier.padding(top = 4.dp),
                    horizontalArrangement = Arrangement.spacedBy(4.dp),
                    verticalArrangement = Arrangement.spacedBy(4.dp)
                ) {
                    phonemes.forEach { phoneme ->
                        PhonemeChip(phoneme)
                    }
                }
            }
            
            // Word-specific feedback
            word.feedback?.let { feedback ->
                Spacer(modifier = Modifier.height(8.dp))
                Text(
                    text = feedback,
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )
            }
        }
    }
}

@Composable
fun PhonemeChip(phoneme: PronunciationPhonemeDto) {
    val backgroundColor = when {
        phoneme.score >= 80 -> Color(0xFF4CAF50).copy(alpha = 0.2f)  // Green
        phoneme.score >= 60 -> Color(0xFFFF9800).copy(alpha = 0.2f)  // Orange
        else -> Color(0xFFF44336).copy(alpha = 0.2f)  // Red
    }
    
    val textColor = when {
        phoneme.score >= 80 -> Color(0xFF2E7D32)
        phoneme.score >= 60 -> Color(0xFFE65100)
        else -> Color(0xFFC62828)
    }
    
    Surface(
        shape = RoundedCornerShape(12.dp),
        color = backgroundColor
    ) {
        Row(
            modifier = Modifier.padding(horizontal = 8.dp, vertical = 4.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            Text(
                text = "/${phoneme.phoneme}/",
                style = MaterialTheme.typography.bodySmall,
                fontWeight = FontWeight.Medium,
                color = textColor,
                fontFamily = NotoSansFont  // ⭐ Important for IPA rendering
            )
            Spacer(modifier = Modifier.width(4.dp))
            Text(
                text = "${phoneme.score.toInt()}",
                style = MaterialTheme.typography.bodySmall,
                fontSize = 10.sp,
                color = textColor
            )
        }
    }
}
```

### 2. ⭐ NEW: IPA Display Component

```kotlin
@Composable
fun IpaTranscriptionCard(word: String, ipa: String) {
    Card(
        modifier = Modifier
            .fillMaxWidth()
            .padding(vertical = 4.dp),
        colors = CardDefaults.cardColors(
            containerColor = MaterialTheme.colorScheme.primaryContainer
        )
    ) {
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(12.dp),
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.SpaceBetween
        ) {
            Column {
                Text(
                    text = word,
                    style = MaterialTheme.typography.titleMedium,
                    fontWeight = FontWeight.Bold
                )
                Text(
                    text = "Pronunciation:",
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onPrimaryContainer.copy(alpha = 0.7f)
                )
            }
            
            Text(
                text = "/$ipa/",
                style = MaterialTheme.typography.titleLarge,
                fontFamily = NotoSansFont,
                color = MaterialTheme.colorScheme.primary,
                fontWeight = FontWeight.Medium
            )
        }
    }
}

// Usage:
word.ipaExpected?.let { ipa ->
    IpaTranscriptionCard(word = word.word, ipa = ipa)
}
```

### 3. Display Detailed Feedback

```kotlin
@Composable
fun DetailedFeedbackSection(detailedFeedback: List<String>?) {
    if (detailedFeedback.isNullOrEmpty()) return
    
    var isExpanded by remember { mutableStateOf(false) }
    
    Card(
        modifier = Modifier
            .fillMaxWidth()
            .padding(vertical = 8.dp)
    ) {
        Column(modifier = Modifier.padding(16.dp)) {
            // Header
            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .clickable { isExpanded = !isExpanded },
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Text(
                        text = "💡",
                        fontSize = 20.sp
                    )
                    Spacer(modifier = Modifier.width(8.dp))
                    Text(
                        text = "Detailed Tips (${detailedFeedback.size})",
                        style = MaterialTheme.typography.titleMedium,
                        fontWeight = FontWeight.SemiBold
                    )
                }
                
                Icon(
                    imageVector = if (isExpanded) 
                        Icons.Default.KeyboardArrowUp 
                    else 
                        Icons.Default.KeyboardArrowDown,
                    contentDescription = if (isExpanded) "Collapse" else "Expand"
                )
            }
            
            // Content (expandable)
            AnimatedVisibility(visible = isExpanded) {
                Column(modifier = Modifier.padding(top = 12.dp)) {
                    detailedFeedback.forEachIndexed { index, tip ->
                        if (index > 0) {
                            Spacer(modifier = Modifier.height(8.dp))
                        }
                        
                        Row(
                            modifier = Modifier.fillMaxWidth(),
                            crossAxisAlignment = Alignment.Top
                        ) {
                            Text(
                                text = "•",
                                style = MaterialTheme.typography.bodyMedium,
                                modifier = Modifier.padding(end = 8.dp)
                            )
                            Text(
                                text = tip,
                                style = MaterialTheme.typography.bodyMedium,
                                modifier = Modifier.weight(1f)
                            )
                        }
                    }
                }
            }
        }
    }
}
```

### 4. Update Main Result Screen

```kotlin
@Composable
fun EnhancedPronunciationResultScreen(
    result: PronunciationResultDto,
    onRetry: () -> Unit,
    onBack: () -> Unit
) {
    Column(
        modifier = Modifier
            .fillMaxSize()
            .verticalScroll(rememberScrollState())
            .padding(16.dp)
    ) {
        // Overall score card (existing)
        OverallScoreCard(result.pronunciationScore)
        
        Spacer(modifier = Modifier.height(16.dp))
        
        // Main feedback (existing, but enhanced)
        FeedbackCard(result.feedback)
        
        Spacer(modifier = Modifier.height(16.dp))
        
        // Score breakdown (existing)
        ScoreBreakdownCard(
            accuracy = result.accuracyScore,
            fluency = result.fluencyScore,
            completeness = result.completenessScore
        )
        
        Spacer(modifier = Modifier.height(16.dp))
        
        // NEW: Detailed feedback section
        DetailedFeedbackSection(result.detailedFeedback)
        
        Spacer(modifier = Modifier.height(16.dp))
        
        // NEW: Word-by-word breakdown with IPA
        Text(
            text = "📝 Word Analysis",
            style = MaterialTheme.typography.titleLarge,
            fontWeight = FontWeight.Bold
        )
        
        Spacer(modifier = Modifier.height(8.dp))
        
        result.words.forEach { word ->
            // Only show words that need practice
            if (word.accuracyScore < 70 || word.errorType != null) {
                PhonemeBreakdownItem(word)
            }
        }
        
        Spacer(modifier = Modifier.height(24.dp))
        
        // Action buttons (existing)
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.spacedBy(8.dp)
        ) {
            OutlinedButton(
                onClick = onRetry,
                modifier = Modifier.weight(1f)
            ) {
                Text("Try Again")
            }
            
            Button(
                onClick = onBack,
                modifier = Modifier.weight(1f)
            ) {
                Text("Done")
            }
        }
    }
}
```

---

## 🎯 IMPROVED SCORING INTERPRETATION

Update your score interpretation to be more nuanced:

```kotlin
fun getPronunciationLevel(score: Float): Pair<String, Color> {
    return when {
        score >= 95 -> "Outstanding 🌟" to Color(0xFF1B5E20)  // Dark green
        score >= 85 -> "Excellent 👏" to Color(0xFF2E7D32)    // Green
        score >= 75 -> "Good 👍" to Color(0xFF388E3C)          // Light green
        score >= 60 -> "Fair 📚" to Color(0xFFFF9800)         // Orange
        score >= 40 -> "Needs Practice 💪" to Color(0xFFE65100) // Deep orange
        else -> "Keep Practicing 🎯" to Color(0xFFF44336)     // Red
    }
}

fun getPhonemeScoreColor(score: Float): Color {
    return when {
        score >= 80 -> Color(0xFF4CAF50)  // Green
        score >= 60 -> Color(0xFFFF9800)  // Orange
        else -> Color(0xFFF44336)         // Red
    }
}
```

---

## 📚 PHONETIC SYMBOLS SUPPORT

Make sure your Android app displays IPA symbols correctly:

### 1. Add Font Support (if needed)

Most modern Android devices support Unicode IPA symbols natively, but if you have issues:

**Option 1: Use Noto Sans Font (Recommended)**

Download `NotoSans-Regular.ttf` from Google Fonts and add to `res/font/`:

```kotlin
// In your theme or typography setup
val NotoSansFont = FontFamily(
    Font(R.font.notosans_regular, FontWeight.Normal)
)

// Use for phoneme and IPA display
Text(
    text = "/${phoneme.phoneme}/",
    fontFamily = NotoSansFont  // Ensures proper rendering
)
```

**Option 2: System Default (Usually Works Fine)**

```kotlin
// Just use default font - most Android devices support IPA
Text(
    text = "/${word.ipaExpected}/",
    // No special font needed on most devices
)
```

### 2. Common IPA Symbols You'll See

```
Vowels: iː, ɪ, e, æ, ɑː, ɒ, ɔː, ʊ, uː, ʌ, ɜː, ə
Consonants: θ, ð, ʃ, ʒ, tʃ, dʒ, ŋ, r, l, w, j
Stress markers: ˈ (primary), ˌ (secondary)
```

### 3. ⭐ IPA Display Best Practices

```kotlin
@Composable
fun IpaText(
    ipa: String,
    modifier: Modifier = Modifier,
    style: TextStyle = MaterialTheme.typography.bodyMedium
) {
    Text(
        text = "/$ipa/",  // Always wrap in slashes
        modifier = modifier,
        style = style,
        fontFamily = NotoSansFont,  // Optional but recommended
        letterSpacing = 0.5.sp  // Slight spacing for readability
    )
}

// Usage:
word.ipaExpected?.let { ipa ->
    IpaText(
        ipa = ipa,
        style = MaterialTheme.typography.titleMedium
    )
}
```

---

## 🧪 TESTING THE NEW FEATURES

### Test Cases:

1. **Good pronunciation** (score > 85)
   - Should show "Excellent" with minimal feedback
   - IPA shown for reference only
   - All phonemes green

2. **Fair pronunciation** (score 60-75)
   - Should highlight 2-3 problem words
   - Show IPA transcription for problem words
   - Show detailed tips for improvement
   - Mix of orange/red phonemes

3. **Poor pronunciation** (score < 60)
   - Multiple problem words highlighted
   - IPA transcription for all problem words
   - Comprehensive feedback with multiple tips
   - Many red phonemes

4. **Missing words** (Omission error)
   - Should show warning about skipped words
   - Show IPA of missing word
   - Prompt user to speak all words

---

## 🔄 MIGRATION CHECKLIST

- [ ] Update `PronunciationDto.kt` with new fields
- [ ] Add `ipa_expected` field to `PronunciationWordDto`
- [ ] Update DTOs to handle nullable `detailedFeedback`
- [ ] Add `PhonemeBreakdownItem` composable
- [ ] Add IPA display to word cards ⭐
- [ ] Add `IpaText` composable for proper IPA rendering ⭐
- [ ] Add `DetailedFeedbackSection` composable
- [ ] Update result screen to show new sections
- [ ] Download and add Noto Sans font (optional)
- [ ] Test with various pronunciation qualities
- [ ] Verify IPA symbols render correctly ⭐
- [ ] Update scoring color scheme (6 levels)
- [ ] Test collapsible detailed feedback UI
- [ ] Update any existing unit tests

---

## 📖 IPA DICTIONARY COVERAGE

The server includes IPA transcriptions for **30+ common business English words**:

✅ Basic: good, morning, hello, please, thank, welcome  
✅ Communication: email, phone, call, meeting, presentation  
✅ Business: business, client, customer, manager, office  
✅ Actions: schedule, interview, appointment, conference  
✅ Documents: report, invoice, contract, agreement  
✅ Descriptive: important, urgent, available, professional

**Note:** If a word is not in the dictionary, the server will build the IPA from Azure's phoneme data (even more accurate!).

---

## 🆘 TROUBLESHOOTING

### Issue: Phonemes field is null
**Solution:** Azure may not always return phoneme-level data. Handle gracefully:
```kotlin
word.phonemes?.let { phonemes ->
    // Show phoneme breakdown
} ?: Text("Phoneme details not available")
```

### Issue: IPA symbols not rendering
**Solution:** Ensure your device/emulator supports Unicode. Test with:
```kotlin
Text("Test: θ ð ʃ ʒ ŋ ɔː ˈmɔːnɪŋ")  // Should display correctly
```

If issues persist, add Noto Sans font to your project.

### Issue: IPA field is null for some words
**Solution:** The server provides IPA for 30+ common words. If a word isn't in the dictionary:
- Azure's phoneme data is used to construct IPA (even better!)
- If neither available, `ipa_expected` will be null

Handle gracefully:
```kotlin
word.ipaExpected?.let { ipa ->
    IpaText(ipa = ipa)
} // Don't show anything if not available
```

### Issue: Too much information overwhelming
**Solution:** Make detailed sections collapsible (already implemented in examples)

---

## 📊 EXPECTED IMPROVEMENTS

**Before:**
```
Score: 82/100
Feedback: "Needs improvement"
Word: morning (55/100)
```

**After:**
```
Score: 82/100
Feedback: "Good pronunciation! 👍"

Word: morning (55/100)
IPA: /ˈmɔːnɪŋ/                    ⭐ NEW
Phonemes:
  /m/ 88    /ɔː/ 45    /n/ 82    /ɪ/ 65    /ŋ/ 70

💡 Detailed Tips:
• Work on 'morning' - Focus on /ɔː/ sound
  Tip: Long 'aw' sound as in 'law'. Round your lips more.
• Practice reading the sentence out loud several times
```

---

## ✅ DONE!

Your Android app now has:
- ✅ Phoneme-level pronunciation analysis
- ✅ **Full IPA (phonetic) transcription for each word** ⭐
- ✅ Detailed, actionable feedback
- ✅ More accurate scoring (6 levels)
- ✅ Phonetic transcription support with proper rendering
- ✅ Word-by-word breakdown with IPA display
- ✅ Professional pronunciation guidance

The server is ready and waiting for your Android app to use these enhanced features! 🚀

**IPA transcription is now fully functional - students can see exactly how each word should be pronounced in standard phonetic notation!** 📖
