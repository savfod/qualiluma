# qualiluma
[![Tests status](https://github.com/savfod/qualiluma/actions/workflows/tests.yml/badge.svg)](https://github.com/savfod/qualiluma/actions/workflows/tests.yml)

Analyze codebase for potential issues with model LLMs.

## Usage

Currently only OpenAI models are supported, set API key with `OPENAI_API_KEY` environment variable.

```bash
pip install qualiluma
OPENAI_API_KEY=your_openai_api_key qualiluma your_code_path
```
