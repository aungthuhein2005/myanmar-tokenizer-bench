# Results

_Dataset: FLORES-200 devtest · 1012 parallel sentences · run 2026-09-29_

**Burmese needs 1.6× to 11.7× as many tokens as English** for the same sentences. With the least efficient tokenizer (Llama 3), the same Burmese text costs 11.7× more, runs about 11.7× slower to generate, and a 128K context window holds 408 Burmese sentences instead of 4,766 English ones.

### Burmese vs English

| Tokenizer | Used by | English tokens | Burmese tokens | Burmese tax | Tokens / syllable | Sentences in 128K (Burmese / English) |
|---|---|---:|---:|---:|---:|---:|
| NLLB-200 | NLLB translation models (reference: trained for 200 languages) | 30,641 | 48,473 | **1.58×** | 0.97 | 2,672 / 4,227 |
| Gemma 3 | Gemma 3 | 28,125 | 66,306 | **2.36×** | 1.33 | 1,953 / 4,605 |
| Gemini 2.5 Flash | Gemini 2.5 | 28,125 | 66,306 | **2.36×** | 1.33 | 1,953 / 4,605 |
| Gemini 3.8 Flash | Gemini 3.8 | 28,125 | 66,306 | **2.36×** | 1.33 | 1,953 / 4,605 |
| OpenAI o200k | GPT-4o, GPT-4.1, o-series, gpt-oss | 26,878 | 85,034 | **3.16×** | 1.70 | 1,523 / 4,819 |
| Phi-4 mini | Phi-4 mini | 26,878 | 85,034 | **3.16×** | 1.70 | 1,523 / 4,819 |
| GPT-5 | GPT-5 | 26,878 | 85,034 | **3.16×** | 1.70 | 1,523 / 4,819 |
| GPT-5.5 | GPT-5.5 | 26,878 | 85,034 | **3.16×** | 1.70 | 1,523 / 4,819 |
| GPT-6 Sol | GPT-6 Sol | 26,878 | 85,034 | **3.16×** | 1.70 | 1,523 / 4,819 |
| Mistral Tekken | Mistral Nemo and later | 27,832 | 90,406 | **3.25×** | 1.81 | 1,432 / 4,654 |
| Claude Opus 5 | Claude Opus 5 | 42,927 | 172,929 | **4.03×** | 3.46 | 749 / 3,017 |
| Claude Sonnet 5 | Claude Sonnet 5 | 42,927 | 172,929 | **4.03×** | 3.46 | 749 / 3,017 |
| DeepSeek V3 | DeepSeek V3 / R1 | 27,046 | 144,243 | **5.33×** | 2.89 | 898 / 4,789 |
| Claude Haiku 4.5 | Claude Haiku 4.5 | 29,894 | 172,181 | **5.76×** | 3.45 | 752 / 4,333 |
| Qwen 3 | Qwen 3 | 27,626 | 247,546 | **8.96×** | 4.96 | 523 / 4,688 |
| OpenAI cl100k | GPT-4, GPT-3.5 | 27,187 | 316,731 | **11.65×** | 6.34 | 408 / 4,764 |
| Llama 3 | Llama 3.x | 27,176 | 316,730 | **11.65×** | 6.34 | 408 / 4,766 |

Identical counts in every language, so these share one tokenizer: OpenAI o200k = Phi-4 mini = GPT-5 = GPT-5.5 = GPT-6 Sol; Gemma 3 = Gemini 2.5 Flash = Gemini 3.8 Flash; Claude Opus 5 = Claude Sonnet 5.

### Every language (tokens as a multiple of English)

| Tokenizer | Burmese | Thai | Khmer | Lao | Hindi | Vietnamese | Chinese (Simplified) |
|---|---:|---:|---:|---:|---:|---:|---:|
| NLLB-200 | **1.58×** | 1.52× | 1.78× | 1.47× | 1.21× | 1.18× | 1.09× |
| Gemma 3 | **2.36×** | 1.58× | 2.67× | 2.56× | 1.30× | 1.36× | 1.08× |
| Gemini 2.5 Flash | **2.36×** | 1.58× | 2.67× | 2.56× | 1.30× | 1.36× | 1.08× |
| Gemini 3.8 Flash | **2.36×** | 1.58× | 2.67× | 2.56× | 1.30× | 1.36× | 1.08× |
| OpenAI o200k | **3.16×** | 1.99× | 3.34× | 8.23× | 1.57× | 1.49× | 1.25× |
| Phi-4 mini | **3.16×** | 1.99× | 3.34× | 8.23× | 1.57× | 1.49× | 1.25× |
| GPT-5 | **3.16×** | 1.99× | 3.34× | 8.23× | 1.57× | 1.49× | 1.25× |
| GPT-5.5 | **3.16×** | 1.99× | 3.34× | 8.23× | 1.57× | 1.49× | 1.25× |
| GPT-6 Sol | **3.16×** | 1.99× | 3.34× | 8.23× | 1.57× | 1.49× | 1.25× |
| Mistral Tekken | **3.25×** | 2.40× | 14.74× | 12.65× | 1.80× | 1.43× | 1.40× |
| Claude Opus 5 | **4.03×** | 2.64× | 3.97× | 3.97× | 2.16× | 1.82× | 1.14× |
| Claude Sonnet 5 | **4.03×** | 2.64× | 3.97× | 3.97× | 2.16× | 1.82× | 1.14× |
| DeepSeek V3 | **5.33×** | 1.80× | 6.83× | 7.97× | 2.79× | 2.12× | 0.94× |
| Claude Haiku 4.5 | **5.76×** | 3.77× | 5.66× | 5.65× | 3.10× | 2.38× | 1.61× |
| Qwen 3 | **8.96×** | 2.58× | 6.50× | 5.69× | 4.43× | 1.44× | 1.00× |
| OpenAI cl100k | **11.65×** | 4.38× | 8.75× | 9.54× | 4.77× | 2.44× | 1.87× |
| Llama 3 | **11.65×** | 2.21× | 8.75× | 8.79× | 2.52× | 1.39× | 1.28× |
