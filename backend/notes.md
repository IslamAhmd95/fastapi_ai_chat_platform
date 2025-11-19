# FastAPI + Gemini AI Notes

## Environment Variables

* `.env` file is recommended for development
* `export VAR=value` sets a temporary terminal variable that ends when terminal session ends
* Use `python-dotenv` to load `.env`


## Why `.env` is Better

* Persistent across sessions
* Easier & less annoying than running `export` each time
* Safer to store secrets locally

---

## Curl Command Explanation

`curl` = command‑line tool to send HTTP requests

Key parts in the Gemini request:

* URL → Gemini model endpoint
* Headers → JSON + API Key
* POST → send data
* JSON body → prompt text

### Expected output

AI returns response in JSON format with generated text.

---

## AI Terminology

| Term                       | Meaning                                                    |
| -------------------------- | ---------------------------------------------------------- |
| Client                     | Tool/library that communicates with a remote service (API) |
| Generative AI              | AI that **creates** text, code, images, etc.               |
| LLM (Large Language Model) | AI brain trained on huge datasets                          |
| API Key                    | Secret key for access                                      |
| Prompt                     | Input you give AI                                          |
| Response                   | Output from AI                                             |

### Example

* `google-generativeai` = Python client to talk to Gemini API

---

## Generative AI vs AI Agents

| Generative AI            | AI Agents                                    |
| ------------------------ | -------------------------------------------- |
| Responds to prompts      | Takes actions using tools + memory           |
| Creates text/code/images | Can do tasks (email, web browse, automation) |
| Needs each instruction   | Can act step‑by‑step                         |

Analogy:

* Generative AI = smart person who answers
* Agent = smart person who answers **and also performs tasks**

---

## Summary

* `.env` for secrets in dev
* `export` is temporary use
* Generative AI creates content
* AI agents use AI + tools to perform actions
* `google-generativeai` = client to talk to Gemini

---

**Next steps**

* Build `/generate` endpoint in FastAPI
* Read `.env` for API key
* Send prompts to Gemini model



```bash

curl -X POST 'http://127.0.0.1:8000/chat' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
        "prompt": "How can i make pizza ?"
    }'

```