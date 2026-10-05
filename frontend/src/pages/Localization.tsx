import { useState } from "react";
import { useQuery, useMutation } from "@tanstack/react-query";
import {
  Globe, Languages, Send, FileText, CheckCircle2,
  Sparkles, RefreshCw,
} from "lucide-react";
import { localizationApi } from "@/api/localization";
import { useToast } from "@/hooks/useToast";
import { errorMessage } from "@/api/client";
import { Card, CardContent, CardTitle, CardDescription } from "@/components/ui/Card";
import { Input, Textarea } from "@/components/ui/Input";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { SUPPORTED_LANGUAGES, LANGUAGE_LABEL } from "@/api/types";

export function LocalizationPage() {
  const { showToast } = useToast();
  const [placeId, setPlaceId] = useState("demo_konark");
  const [language, setLanguage] = useState("en");
  const [translateText, setTranslateText] = useState("");
  const [sourceLang, setSourceLang] = useState("en");
  const [targetLang, setTargetLang] = useState("hi");
  const [translated, setTranslated] = useState<{ text: string; cached: boolean } | null>(null);

  const contentQ = useQuery({
    queryKey: ["localization", placeId, language],
    queryFn: () => localizationApi.getContent(placeId, language),
  });

  const translateMutation = useMutation({
    mutationFn: () =>
      localizationApi.translate({
        text: translateText.trim(),
        source_language: sourceLang,
        target_language: targetLang,
      }),
    onSuccess: (res: any) => {
      setTranslated({ text: res.text, cached: res.cached });
      showToast({
        type: "success",
        title: res.cached ? "From cache!" : "Translated!",
        message: `${LANGUAGE_LABEL[sourceLang] ?? sourceLang} → ${LANGUAGE_LABEL[targetLang] ?? targetLang}`,
      });
    },
    onError: (err: any) => showToast({ type: "error", title: "Translation failed", message: errorMessage(err) }),
  });

  return (
    <div className="mx-auto max-w-5xl px-4 sm:px-6 space-y-8">
      <header>
        <h1 className="text-3xl sm:text-4xl font-extrabold tracking-tight flex items-center gap-2">
          <Globe className="w-8 h-8" aria-hidden="true" /> Localization
        </h1>
        <p className="mt-1 text-slate-600">
          GET /api/localization/:place/content/:lang · POST /api/translate · SHA-256 cache
        </p>
      </header>

      {/* Translation playground */}
      <Card variant="glass">
        <CardContent>
          <CardTitle className="flex items-center gap-2">
            <Languages className="w-5 h-5" aria-hidden="true" /> Live translation
          </CardTitle>
          <CardDescription>POST /api/translate · same-language requests skip the provider entirely.</CardDescription>
          <div className="mt-4 grid gap-4 sm:grid-cols-2">
            <div>
              <label className="block text-sm font-medium mb-1.5">From</label>
              <select
                value={sourceLang}
                onChange={(e) => setSourceLang(e.target.value)}
                className="w-full px-4 py-3 rounded-2xl border-2 border-slate-200/80 bg-white/90 focus:outline-none focus:border-terracotta-500"
              >
                {SUPPORTED_LANGUAGES.map((l) => <option key={l.code} value={l.code}>{l.label}</option>)}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium mb-1.5">To</label>
              <select
                value={targetLang}
                onChange={(e) => setTargetLang(e.target.value)}
                className="w-full px-4 py-3 rounded-2xl border-2 border-slate-200/80 bg-white/90 focus:outline-none focus:border-terracotta-500"
              >
                {SUPPORTED_LANGUAGES.map((l) => <option key={l.code} value={l.code}>{l.label}</option>)}
              </select>
            </div>
          </div>
          <Textarea
            label="Text to translate"
            value={translateText}
            onChange={(e) => setTranslateText(e.target.value)}
            placeholder="e.g. Welcome to the Sun Temple of Konark"
            rows={3}
          />
          <Button
            onClick={() => translateMutation.mutate()}
            loading={translateMutation.isPending}
            className="mt-3"
          >
            <Send className="w-4 h-4" aria-hidden="true" /> Translate
          </Button>

          {translated && (
            <div className="mt-4 rounded-2xl border-2 border-terracotta-300 bg-terracotta-50/60 p-4">
              <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">
                {translated.cached ? "Cached result" : "Fresh translation"}
              </p>
              <p className="mt-1 text-lg text-slate-800">{translated.text}</p>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Place content */}
      <Card variant="glass">
        <CardContent>
          <CardTitle className="flex items-center gap-2">
            <FileText className="w-5 h-5" aria-hidden="true" /> Localized place content
          </CardTitle>
          <CardDescription>GET /api/localization/:place/content/:language</CardDescription>
          <div className="mt-4 grid gap-4 sm:grid-cols-3">
            <Input label="Place ID" value={placeId} onChange={(e) => setPlaceId(e.target.value)} />
            <div>
              <label className="block text-sm font-medium mb-1.5">Language</label>
              <select
                value={language}
                onChange={(e) => setLanguage(e.target.value)}
                className="w-full px-4 py-3 rounded-2xl border-2 border-slate-200/80 bg-white/90"
              >
                {SUPPORTED_LANGUAGES.map((l) => <option key={l.code} value={l.code}>{l.label}</option>)}
              </select>
            </div>
            <div className="flex items-end">
              <Button variant="outline" onClick={() => contentQ.refetch()} loading={contentQ.isFetching}>
                <RefreshCw className="w-4 h-4" aria-hidden="true" /> Reload
              </Button>
            </div>
          </div>

          {contentQ.isLoading && <p className="mt-4 text-slate-500">Loading content…</p>}
          {contentQ.error && (
            <div className="mt-4 rounded-2xl border-2 border-slate-200 bg-slate-50 p-4">
              <p className="text-slate-600">No localized content for this place & language yet.</p>
            </div>
          )}
          {contentQ.data && (
            <div className="mt-4 rounded-2xl border-2 border-emerald-200 bg-emerald-50/50 p-4">
              <div className="flex items-center gap-2">
                <CheckCircle2 className="w-5 h-5 text-emerald-600" aria-hidden="true" />
                <p className="font-bold text-lg">{contentQ.data.title}</p>
                <Badge variant="success">{LANGUAGE_LABEL[contentQ.data.language] ?? contentQ.data.language}</Badge>
              </div>
              <p className="mt-2 text-slate-700">{contentQ.data.description}</p>
              {contentQ.data.rules && <p className="mt-2 text-sm text-slate-600"><strong>Rules:</strong> {contentQ.data.rules}</p>}
              {contentQ.data.tips && <p className="mt-2 text-sm text-slate-600"><strong>Tips:</strong> {contentQ.data.tips}</p>}
              <p className="mt-2 text-xs text-slate-400">Source: {contentQ.data.source}</p>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
