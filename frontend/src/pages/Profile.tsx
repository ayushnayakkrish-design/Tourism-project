import { useState, useEffect } from "react";
import { User, Globe, Bell, ShieldCheck, Save } from "lucide-react";
import { useAuth } from "@/hooks/useAuth";
import { useToast } from "@/hooks/useToast";
import { usersApi } from "@/api/auth";
import { LANGUAGE_LABEL, SUPPORTED_LANGUAGES } from "@/api/types";
import { errorMessage } from "@/api/client";
import { Card, CardContent, CardTitle, CardDescription } from "@/components/ui/Card";
import { Input, Textarea } from "@/components/ui/Input";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";

export function ProfilePage() {
  const { user, preferences, refreshUser, updatePreferences } = useAuth();
  const { showToast } = useToast();
  const [displayName, setDisplayName] = useState("");
  const [bio, setBio] = useState("");
  const [saving, setSaving] = useState(false);
  const [prefSaving, setPrefSaving] = useState(false);
  const [lang, setLang] = useState("en");
  const [voice, setVoice] = useState(true);

  useEffect(() => {
    if (user) {
      setDisplayName(user.display_name || "");
      setBio(user.bio || "");
    }
  }, [user]);

  useEffect(() => {
    if (preferences) {
      setLang(preferences.language || "en");
      setVoice(preferences.voice_enabled);
    }
  }, [preferences]);

  const saveProfile = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    try {
      await usersApi.updateProfile({
        display_name: displayName.trim() || undefined,
        bio: bio.trim(),
      });
      await refreshUser();
      showToast({ type: "success", title: "Profile updated" });
    } catch (err) {
      showToast({ type: "error", title: "Update failed", message: errorMessage(err) });
    } finally {
      setSaving(false);
    }
  };

  const savePrefs = async () => {
    setPrefSaving(true);
    try {
      await updatePreferences({ language: lang, voice_enabled: voice });
      showToast({ type: "success", title: "Preferences saved" });
    } catch (err) {
      showToast({ type: "error", title: "Save failed", message: errorMessage(err) });
    } finally {
      setPrefSaving(false);
    }
  };

  return (
    <div className="mx-auto max-w-4xl px-4 sm:px-6 space-y-6">
      <header>
        <h1 className="text-3xl sm:text-4xl font-extrabold tracking-tight">Profile & settings</h1>
        <p className="mt-1 text-slate-600">GET/PATCH /api/users/me · your identity, your preferences.</p>
      </header>

      <Card variant="glass">
        <CardContent className="flex items-center gap-4">
          <div className="w-16 h-16 rounded-3xl bg-black text-white flex items-center justify-center text-2xl font-extrabold">
            {(user?.display_name || user?.email || "U").charAt(0).toUpperCase()}
          </div>
          <div className="flex-1">
            <h2 className="text-xl font-bold">{user?.display_name || "Traveler"}</h2>
            <p className="text-sm text-slate-500">{user?.email}</p>
          </div>
          <Badge variant="info">{user?.role}</Badge>
        </CardContent>
      </Card>

      <div className="grid gap-6 md:grid-cols-2">
        <Card variant="glass">
          <CardContent>
            <CardTitle className="flex items-center gap-2">
              <User className="w-5 h-5" aria-hidden="true" /> Public profile
            </CardTitle>
            <CardDescription>PATCH /api/users/me</CardDescription>
            <form onSubmit={saveProfile} className="mt-4 space-y-4">
              <Input
                label="Display name"
                value={displayName}
                onChange={(e) => setDisplayName(e.target.value)}
                maxLength={80}
              />
              <Textarea
                label="Bio"
                value={bio}
                onChange={(e) => setBio(e.target.value)}
                placeholder="Tell fellow travelers about yourself…"
                rows={4}
              />
              <Button type="submit" loading={saving}>
                <Save className="w-4 h-4" aria-hidden="true" /> Save profile
              </Button>
            </form>
          </CardContent>
        </Card>

        <div className="space-y-6">
          <Card variant="glass">
            <CardContent>
              <CardTitle className="flex items-center gap-2">
                <Globe className="w-5 h-5" aria-hidden="true" /> Language & voice
              </CardTitle>
              <CardDescription>PATCH /api/users/me/preferences</CardDescription>
              <div className="mt-4 space-y-4">
                <div>
                  <label htmlFor="pref-lang" className="block text-sm font-medium mb-1.5">
                    Preferred language
                  </label>
                  <select
                    id="pref-lang"
                    value={lang}
                    onChange={(e) => setLang(e.target.value)}
                    className="w-full px-4 py-3 rounded-2xl border-2 border-slate-200/80 bg-white/90 focus:outline-none focus:border-terracotta-500"
                  >
                    {SUPPORTED_LANGUAGES.map((l) => (
                      <option key={l.code} value={l.code}>
                        {l.label} ({l.code})
                      </option>
                    ))}
                  </select>
                  <p className="mt-1 text-xs text-slate-500">
                    Current: {LANGUAGE_LABEL[preferences?.language ?? "en"] ?? "English"}
                  </p>
                </div>
                <label className="flex items-center gap-3 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={voice}
                    onChange={(e) => setVoice(e.target.checked)}
                    className="w-5 h-5 rounded accent-terracotta-600"
                  />
                  <span className="text-sm font-medium flex items-center gap-2">
                    <Bell className="w-4 h-4" aria-hidden="true" /> Enable voice queries
                  </span>
                </label>
                <Button onClick={savePrefs} loading={prefSaving}>
                  <Save className="w-4 h-4" aria-hidden="true" /> Save preferences
                </Button>
              </div>
            </CardContent>
          </Card>

          <Card variant="glass">
            <CardContent>
              <CardTitle className="flex items-center gap-2">
                <ShieldCheck className="w-5 h-5" aria-hidden="true" /> Account
              </CardTitle>
              <CardDescription>Your role controls what you can do across Wandor.</CardDescription>
              <div className="mt-3 space-y-2 text-sm">
                <p>
                  <span className="font-semibold">User ID:</span>{" "}
                  <code className="px-2 py-0.5 rounded-lg bg-slate-100 text-xs break-all">{user?.id}</code>
                </p>
                <p><span className="font-semibold">Role:</span> <Badge variant="info">{user?.role}</Badge></p>
                <p className="text-slate-500">
                  Role upgrades are performed by administrators only — never from this page.
                </p>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
