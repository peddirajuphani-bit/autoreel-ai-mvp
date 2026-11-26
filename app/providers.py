import json
from abc import ABC, abstractmethod

class ContentProvider(ABC):
    @abstractmethod
    def generate(self, profile): ...

TEXT_FIELDS = ["topic", "hook", "title", "script", "caption", "hashtags", "cover_text", "cta"]

def normalize_plan(data, target_duration):
    if not isinstance(data, dict):
        raise ValueError("AI response must be a JSON object")
    plan = {k: str(data.get(k) or "") for k in TEXT_FIELDS}
    try:
        plan["quality_score"] = max(0.0, min(100.0, float(data.get("quality_score") or 0)))
    except (TypeError, ValueError):
        raise ValueError("AI response has invalid quality_score")
    scenes = data.get("scenes")
    if not isinstance(scenes, list) or not scenes:
        raise ValueError("AI response must contain a non-empty scenes list")
    parsed = []
    for s in scenes:
        if isinstance(s, dict):
            headline, voiceover = s.get("headline"), s.get("voiceover_text", "")
        elif isinstance(s, (list, tuple)) and len(s) == 3:
            headline, voiceover = s[0], s[1]
        else:
            raise ValueError("AI response scenes must be [headline, voiceover, duration]")
        if not headline or not str(headline).strip():
            raise ValueError("AI response scene is missing a headline")
        parsed.append((str(headline), str(voiceover), 1))
    total_target = max(7, int(target_duration))
    weights = []
    for s in scenes:
        try:
            weights.append(max(1, int(float(s[2] if isinstance(s, (list, tuple)) else s.get("duration", 1)))))
        except (TypeError, ValueError, IndexError, KeyError):
            weights.append(1)
    total = sum(weights)
    scaled = [max(1, int(round(w * total_target / total))) for w in weights]
    drift = total_target - sum(scaled)
    scaled[scaled.index(max(scaled))] += drift if scaled[scaled.index(max(scaled))] + drift >= 1 else 0
    plan["scenes"] = [(h, v, d) for (h, v, _), d in zip(parsed, scaled)]
    plan["script"] = plan["script"] or " ".join(v for _, v, _ in plan["scenes"])
    return plan

class MockContentProvider(ContentProvider):
    def generate(self, p):
        topic = f"5 practical AI skills for {p.target_audience}"
        hook = "Your next career advantage may not be another certificate."
        scenes = [
          ("Stop collecting certificates", "Your next career advantage may not be another certificate.", 4),
          ("Skill 1: Prompt clearly", "Learn to give AI clear context, constraints and examples.", 4),
          ("Skill 2: Verify outputs", "Always check facts, numbers and sources before using an AI answer.", 4),
          ("Skill 3: Automate workflows", "Connect AI to a repeatable work process, not just one-off questions.", 5),
          ("Skill 4: Protect data", "Never paste confidential company or candidate information into unapproved tools.", 5),
          ("Skill 5: Show outcomes", "Measure time saved, quality improved and business impact.", 4),
          ("Save this checklist", "Save this Reel and choose one skill to practise this week.", 4),
        ]
        script = " ".join(x[1] for x in scenes)
        return {
          "topic": topic, "hook": hook, "title": "5 AI Skills That Matter at Work",
          "script": script,
          "caption": "AI fluency is becoming a practical workplace skill. Start with one capability, use it responsibly, and measure the outcome.",
          "hashtags": "#AISkills #CareerGrowth #TechCareers #FutureOfWork #IndiaTech",
          "cover_text": "5 AI Skills You Need", "cta": "Save this and practise one skill this week.",
          "quality_score": 88, "scenes": scenes
        }


def build_prompt(p):
    return (
        f"Create a {p.preferred_duration}-second Instagram Reel plan for the brand "
        f"'{p.brand_name}' in the genre \"{p.primary_genre}\". Target audience: "
        f"{p.target_audience}. Country: {p.country}. Language: {p.language}. Tone: {p.tone}. "
        f"Objective: {p.objective}. Topics to include: {p.topics_include or 'none'}. "
        f"Topics to avoid: {p.topics_exclude or 'none'}.\n\n"
        "Return ONLY a JSON object with exactly these keys:\n"
        "- topic (string, <=200 chars)\n- hook (string, one punchy first line)\n"
        "- title (string)\n- script (string, all voiceover text joined)\n"
        "- caption (string, Instagram caption)\n- hashtags (string, space-separated #tags)\n"
        "- cover_text (string, <=60 chars)\n- cta (string, call to action)\n"
        f"- quality_score (number 0-100)\n"
        f"- scenes: a list of exactly 7 items, each a [headline, voiceover_text, duration] "
        f"array where durations are integers and all 7 durations sum to {p.preferred_duration}.\n\n"
        "Respond with JSON only, no markdown fences, no commentary."
    )

class GeminiContentProvider(ContentProvider):
    def __init__(self, api_key, model, base_url="https://generativelanguage.googleapis.com/v1beta"):
        import httpx
        self.api_key, self.model, self.base_url = api_key, model, base_url
        self.httpx = httpx

    def generate(self, p):
        with self.httpx.Client(timeout=90) as c:
            r = c.post(
                f"{self.base_url}/models/{self.model}:generateContent",
                params={"key": self.api_key},
                json={
                    "contents": [{"parts": [{"text": build_prompt(p)}]}],
                    "generationConfig": {"responseMimeType": "application/json", "temperature": 0.8},
                },
            )
        if r.status_code == 401 or r.status_code == 403:
            raise ValueError("Gemini rejected the API key (check GEMINI_API_KEY)")
        if r.status_code == 429:
            raise ValueError("Gemini rate limit reached; retry shortly")
        if r.status_code >= 400:
            raise ValueError(f"Gemini API error {r.status_code}")
        try:
            text = r.json()["candidates"][0]["content"]["parts"][0]["text"]
        except (KeyError, IndexError, TypeError):
            raise ValueError("Gemini returned an unexpected response shape")
        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            raise ValueError("Gemini returned non-JSON content")
        return normalize_plan(data, p.preferred_duration)
