import { useState, useRef, useEffect } from "react";
import { useMutation } from "@tanstack/react-query";
import {
  Mic, MicOff, Send, Sparkles, MapPin,
  Route, Users, Calendar, AlertTriangle,
  Volume2,
} from "lucide-react";
import { voiceApi } from "@/api/localization";
import { useToast } from "@/hooks/useToast";
import { errorMessage } from "@/api/client";
import { Card, CardContent, CardTitle, CardDescription } from "@/components/ui/Card";
import { Input } from "@/components/ui/Input";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";

const INTENT_ICONS: Record<string, any> = {
  PLACE_SEARCH: MapPin,
  NEARBY_SEARCH: MapPin,
  ROUTE_REQUEST: Route,
  ITINERARY_REQUEST: Calendar,
  CROWD_QUERY: Users,
  BEST_TIME_QUERY: Users,
  REWARD_QUERY: Sparkles,
  PLACE_INFORMATION: MapPin,
  COMMUNITY_SEARCH: Users,
};

export function VoicePage() {
  const { showToast } = useToast();
  const [query, setQuery] = useState("");
  const [language, setLanguage] = useState("en");
  const [recording, setRecording] = useState(false);
  const [audioBlob, setAudioBlob] = useState<Blob | null>(null);
  const [transcript, setTranscript] = useState<string | null>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<BlobPart[]>([]);

  const textQueryMutation = useMutation({
    mutationFn: () => voiceApi.textQuery({ query: query.trim(), language }),
    onSuccess: (res) => {
      setTranscript(res.transcription || res.parameters?.query || query);
      showToast({ type: "success", title: `Intent: ${res.intent}` });
    },
    onError: (err) => showToast({ type: "error", title: "Voice query failed", message: errorMessage(err) }),
  });

  const audioQueryMutation = useMutation({
    mutationFn: async () => {
      if (!audioBlob) throw new Error("No audio recorded");
      const buffer = await audioBlob.arrayBuffer();
      const base64 = btoa(String.fromCharCode(...new Uint8Array(buffer)));
      return voiceApi.audioQuery({ audio_base64: base64, language });
    },
    onSuccess: (res) => {
      setTranscript(res.transcription || null);
      showToast({ type: "success", title: `Audio intent: ${res.intent}` });
    },
    onError: (err) => showToast({ type: "error", title: "Audio query failed", message: errorMessage(err) }),
  });

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const rec = new MediaRecorder(stream);
      chunksRef.current = [];
      rec.ondataavailable = (e) => chunksRef.current.push(e.data);
      rec.onstop = () => {
        const blob = new Blob(chunksRef.current, { type: "audio/webm" });
        setAudioBlob(blob);
        stream.getTracks().forEach((t) => t.stop());
      };
      rec.start();
      mediaRecorderRef.current = rec;
      setRecording(true);
    } catch (err) {
      showToast({ type: "error", title: "Mic unavailable", message: errorMessage(err) });
    }
  };

  const stopRecording = () => {
    mediaRecorderRef.current?.stop();
    setRecording(false);
  };

  return (
    <div className="mx-auto max-w-4xl px-4 sm:px-6 space-y-8">
      <header>
        <h1 className="text-3xl sm:text-4xl font-extrabold tracking-tight flex items-center gap-2">
          <Volume2 className="w-8 h-8" aria-hidden="true" /> Voice queries
        </h1>
        <p className="mt-1 text-slate-600">POST /api/voice/query · POST /api/voice/audio · NLP intent extraction</p>
      </header>

      <Card variant="glass">
        <CardContent>
          <CardTitle className="flex items-center gap-2">
            <Sparkles className="w-5 h-5" aria-hidden="true" /> Type a query
          </CardTitle>
          <CardDescription>Backend extracts intent with rules or AI depending on configuration.</CardDescription>
          <div className="mt-4 space-y-3">
            <Input
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="e.g. Find quiet temples near Puri this weekend"
            />
            <div className="flex flex-wrap items-center gap-2">
              <select
                value={language}
                onChange={(e) => setLanguage(e.target.value)}
                className="px-4 py-3 rounded-2xl border-2 border-slate-200/80 bg-white/90"
              >
                <option value="en">English</option>
                <option value="hi">हिन्दी</option>
                <option value="or">ଓଡ଼ିଆ</option>
              </select>
              <Button
                onClick={() => textQueryMutation.mutate()}
                loading={textQueryMutation.isPending}
              >
                <Send className="w-4 h-4" aria-hidden="true" /> Send query
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      <Card variant="glass">
        <CardContent>
          <CardTitle className="flex items-center gap-2">
            <Mic className="w-5 h-5" aria-hidden="true" /> Speak a query
          </CardTitle>
          <CardDescription>Audio is base64-encoded to POST /api/voice/audio.</CardDescription>
          <div className="mt-4 flex flex-wrap items-center gap-3">
            <Button
              onClick={recording ? stopRecording : startRecording}
              variant={recording ? "danger" : "secondary"}
              size="lg"
            >
              {recording ? <MicOff className="w-5 h-5" aria-hidden="true" /> : <Mic className="w-5 h-5" aria-hidden="true" />}
              {recording ? "Stop recording" : "Start recording"}
            </Button>
            {audioBlob && (
              <Button
                onClick={() => audioQueryMutation.mutate()}
                loading={audioQueryMutation.isPending}
                size="lg"
              >
                <Send className="w-4 h-4" aria-hidden="true" /> Submit audio
              </Button>
            )}
            {recording && (
              <span className="flex items-center gap-2 text-red-600 font-semibold">
                <span className="w-3 h-3 rounded-full bg-red-500 animate-pulse" aria-hidden="true" />
                Recording…
              </span>
            )}
          </div>
          {audioBlob && (
            <audio controls className="mt-4 w-full" src={URL.createObjectURL(audioBlob)} />
          )}
        </CardContent>
      </Card>

      {(textQueryMutation.data || audioQueryMutation.data) && (
        <Card variant="glass">
          <CardContent>
            <CardTitle>Extracted intent</CardTitle>
            {(() => {
              const data = textQueryMutation.data || audioQueryMutation.data;
              if (!data) return null;
              const IntentIcon = INTENT_ICONS[data.intent || ""] || Sparkles;
              return (
                <div className="mt-3 space-y-3">
                  <div className="flex items-center gap-2">
                    <IntentIcon className="w-5 h-5 text-terracotta-600" aria-hidden="true" />
                    <Badge variant="info" size="lg">{data.intent}</Badge>
                  </div>
                  {data.parameters && (
                    <div className="rounded-2xl bg-slate-50 border border-slate-200 p-4 text-sm">
                      <p><strong>Query:</strong> {data.parameters.query}</p>
                      {data.parameters.category && <p><strong>Category:</strong> {data.parameters.category}</p>}
                      {data.parameters.location && <p><strong>Location:</strong> {data.parameters.location}</p>}
                      <p><strong>Open now:</strong> {data.parameters.open_now ? "Yes" : "No"}</p>
                    </div>
                  )}
                  {data.transcription && (
                    <p className="text-sm text-slate-600 italic">Transcription: “{data.transcription}”</p>
                  )}
                  {Array.isArray(data.places) && data.places.length > 0 && (
                    <div className="space-y-2">
                      {data.places.map((p: any) => (
                        <div key={p.place_id} className="flex items-center gap-2 p-2 rounded-xl bg-white/70 border border-white/40">
                          <MapPin className="w-4 h-4 text-terracotta-600" aria-hidden="true" />
                          <span className="font-medium">{p.name}</span>
                          <span className="text-xs text-slate-500">{p.address}</span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              );
            })()}
          </CardContent>
        </Card>
      )}
    </div>
  );
}
