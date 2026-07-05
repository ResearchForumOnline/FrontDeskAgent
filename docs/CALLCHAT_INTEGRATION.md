# CallChat Integration

FrontDeskAgent can share OpenZero and Voicebox with CallChat ZERO.

The practical deployment pattern is:

```text
FrontDeskAgent
  -> OpenZero local LLM bridge
  -> optional Voicebox speech

CallChat ZERO
  -> Matrix rooms
  -> @zero:callchat.org
  -> OpenZero local LLM bridge
  -> optional Voicebox speech
```

## What This Enables

- Front desk leads, appointment requests, handoffs, and voice alerts can use the same local OpenZero brain.
- CallChat rooms can use Zero Bot for approved-room Q&A, summaries, Shield help, and optional voice replies.
- Businesses can use CallChat as the secure messaging layer around FrontDeskAgent workflows.
- The stack can run without paid cloud AI by default when OpenZero and local models are available.

## Recommended Environment

FrontDeskAgent:

```env
LLM_BACKEND=auto
OPENZERO_LLM_URL=http://127.0.0.1:1024/v1/chat/completions
OPENZERO_MODEL=local
VOICE_TTS_PROVIDER=voicebox
VOICEBOX_URL=http://127.0.0.1:17493
VOICEBOX_ENDPOINT=/generate
```

CallChat Zero Bot:

```env
MATRIX_HOMESERVER=https://callchat.org
MATRIX_USER_ID=@zero:callchat.org
CALLCHAT_BOT_ALLOWED_ROOMS=#zero-bot-lab:callchat.org
OPENZERO_LLM_URL=http://127.0.0.1:1024/v1/chat/completions
VOICEBOX_URL=http://127.0.0.1:17493
```

Store real passwords and API keys outside Git.

## Safety Boundary

- FrontDeskAgent customer data should not be posted into public Matrix rooms automatically.
- CallChat Shield passwords, pattern images, recovery phrases, Matrix signing keys, and database credentials must never be sent to the bot.
- Voice output should begin command-triggered, not automatic for every message.
- Public bots should be witty and useful, not abusive, spammy, or unsafe.

## Product Story

FrontDeskAgent handles business intake. CallChat handles sovereign messaging. OpenZero supplies the local AI lane. Voicebox supplies local speech. Together they create a self-hosted business communication stack with a realistic CPU-first path.
