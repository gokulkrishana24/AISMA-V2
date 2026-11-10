"use client";

import { useState } from "react";
import { AppLayout } from "@/components/layout/app-layout";
import {
  Palette,
  Sparkles,
  Sliders,
  Image as ImageIcon,
  Video,
  Layers,
  AlertTriangle,
  CheckCircle2,
  Cpu,
  Copy,
  ExternalLink,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";

export default function CreativeStudioPage() {
  const [activeTab, setActiveTab] = useState<"image" | "video" | "assets">("image");
  const [promptSubject, setPromptSubject] = useState(
    "Futuristic dark navy holographic AI command center with data streams, cinematic lighting, ultra-detailed 8k octane render"
  );
  const [stylePreset, setStylePreset] = useState("Dark Enterprise Tech");
  const [aspectRatio, setAspectRatio] = useState("16:9");
  const [isGenerating, setIsGenerating] = useState(false);
  const [localBackendAvailable, setLocalBackendAvailable] = useState(false); // Honest local status

  const [generatedPromptBlueprint, setGeneratedPromptBlueprint] = useState<string | null>(null);

  const handleBuildPrompt = () => {
    setIsGenerating(true);
    setTimeout(() => {
      setGeneratedPromptBlueprint(
        `PROMPT BLUEPRINT: (${promptSubject}), architectural symmetry, dark navy and cyan volumetric illumination, Ray-traced reflections, Unreal Engine 5 aesthetic, photorealistic, shot on 35mm Hasselblad --ar ${aspectRatio} --v 6.0 --style raw\nNEGATIVE PROMPT: blurry, low resolution, watermark, cartoon, oversaturated, disfigured, text errors`
      );
      setIsGenerating(false);
    }, 600);
  };

  return (
    <AppLayout>
      <div className="space-y-8">
        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 pb-2 border-b border-slate-800/80">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <Badge variant="cyan" className="text-[10px] tracking-wider uppercase font-bold">
                Creative Studio
              </Badge>
              <span className="text-xs text-slate-400">
                Visual Campaign Formulations & Local Prompt Engineering
              </span>
            </div>
            <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
              Creative Studio
            </h1>
          </div>

          <div className="flex items-center gap-2">
            {localBackendAvailable ? (
              <Badge variant="success" className="gap-1.5 text-xs font-mono">
                <Cpu className="w-3.5 h-3.5" />
                Local SDXL Engine Ready
              </Badge>
            ) : (
              <Badge variant="warning" className="gap-1.5 text-xs font-mono">
                <AlertTriangle className="w-3.5 h-3.5 text-amber-400" />
                Local SDXL Server Offline (Blueprint Mode)
              </Badge>
            )}
          </div>
        </div>

        {/* Tab Buttons */}
        <div className="flex border-b border-slate-800 space-x-6 text-sm font-medium">
          <button
            onClick={() => setActiveTab("image")}
            className={`pb-3 flex items-center gap-2 transition-colors ${
              activeTab === "image"
                ? "border-b-2 border-blue-500 text-white font-bold"
                : "text-slate-400 hover:text-slate-200"
            }`}
          >
            <ImageIcon className="w-4 h-4 text-blue-400" />
            Image Prompt Builder & Specs
          </button>
          <button
            onClick={() => setActiveTab("video")}
            className={`pb-3 flex items-center gap-2 transition-colors ${
              activeTab === "video"
                ? "border-b-2 border-blue-500 text-white font-bold"
                : "text-slate-400 hover:text-slate-200"
            }`}
          >
            <Video className="w-4 h-4 text-cyan-400" />
            Video Script Generator
          </button>
          <button
            onClick={() => setActiveTab("assets")}
            className={`pb-3 flex items-center gap-2 transition-colors ${
              activeTab === "assets"
                ? "border-b-2 border-blue-500 text-white font-bold"
                : "text-slate-400 hover:text-slate-200"
            }`}
          >
            <Layers className="w-4 h-4 text-purple-400" />
            Asset Library & Brand Specs
          </button>
        </div>

        {/* Tab 1: Image Prompt Builder */}
        {activeTab === "image" && (
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
            <div className="lg:col-span-7 space-y-6">
              <Card>
                <CardHeader>
                  <CardTitle className="text-base text-white">Visual Campaign Concept Builder</CardTitle>
                  <CardDescription>
                    Formulate detailed image generation prompts adhering to Brand OS guidelines
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div>
                    <label className="text-xs font-semibold uppercase text-slate-300 block mb-1.5">
                      Subject & Scene Description
                    </label>
                    <Textarea
                      value={promptSubject}
                      onChange={(e) => setPromptSubject(e.target.value)}
                      rows={3}
                    />
                  </div>

                  {/* Aspect Ratio Options */}
                  <div>
                    <label className="text-xs font-semibold uppercase text-slate-300 block mb-2">
                      Aspect Ratio Specification
                    </label>
                    <div className="grid grid-cols-4 gap-2">
                      {[
                        { ratio: "1:1", label: "Square (1:1)", channel: "Feed / Avatar" },
                        { ratio: "16:9", label: "Landscape (16:9)", channel: "LinkedIn / YouTube" },
                        { ratio: "9:16", label: "Vertical (9:16)", channel: "Reels / TikTok" },
                        { ratio: "4:5", label: "Portrait (4:5)", channel: "Instagram Feed" },
                      ].map((item) => (
                        <button
                          key={item.ratio}
                          type="button"
                          onClick={() => setAspectRatio(item.ratio)}
                          className={`p-2.5 rounded-lg border text-left transition-all ${
                            aspectRatio === item.ratio
                              ? "border-blue-500 bg-blue-600/20 text-blue-300 shadow-glow-blue"
                              : "border-slate-800 bg-navy-950/60 text-slate-400 hover:border-slate-700"
                          }`}
                        >
                          <div className="font-bold text-xs">{item.label}</div>
                          <div className="text-[10px] text-slate-500 mt-0.5">{item.channel}</div>
                        </button>
                      ))}
                    </div>
                  </div>

                  <Button
                    onClick={handleBuildPrompt}
                    disabled={isGenerating}
                    className="w-full bg-blue-600 hover:bg-blue-500 shadow-glow-blue font-semibold text-xs h-10"
                  >
                    <Sparkles className="w-3.5 h-3.5 mr-1.5" />
                    {isGenerating ? "Compiling Blueprint..." : "Generate Prompt Blueprint"}
                  </Button>
                </CardContent>
              </Card>

              {/* Generated Blueprint Box */}
              {generatedPromptBlueprint && (
                <Card className="border-cyan-500/30">
                  <CardHeader className="pb-2">
                    <div className="flex items-center justify-between">
                      <CardTitle className="text-sm text-cyan-300 flex items-center gap-1.5">
                        <CheckCircle2 className="w-4 h-4 text-cyan-400" />
                        Engine-Optimized Prompt Specification
                      </CardTitle>
                      <Button
                        size="sm"
                        variant="ghost"
                        className="text-xs h-7 text-cyan-300"
                        onClick={() => {
                          navigator.clipboard.writeText(generatedPromptBlueprint);
                          alert("Copied to clipboard!");
                        }}
                      >
                        <Copy className="w-3.5 h-3.5 mr-1" /> Copy
                      </Button>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <pre className="p-3.5 rounded-lg bg-navy-950 border border-slate-800 font-mono text-xs text-slate-200 whitespace-pre-wrap leading-relaxed">
                      {generatedPromptBlueprint}
                    </pre>
                  </CardContent>
                </Card>
              )}
            </div>

            {/* Right Column: Local Inference Status & Safe Fallback Notice */}
            <div className="lg:col-span-5 space-y-6">
              <Card>
                <CardHeader className="pb-3">
                  <CardTitle className="text-sm text-white flex items-center gap-2">
                    <Cpu className="w-4 h-4 text-blue-400" />
                    Local Image Generation Backend Status
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="p-4 rounded-xl border border-amber-500/30 bg-amber-950/20 space-y-2">
                    <div className="flex items-center gap-2 text-xs font-bold text-amber-300">
                      <AlertTriangle className="w-4 h-4 text-amber-400" />
                      Strict Honest Rendering Enforcement
                    </div>
                    <p className="text-[11px] text-amber-200/80 leading-relaxed">
                      As mandated by system governance: This platform <strong>never fakes or simulates generated image outputs</strong> when the local diffusion server is disconnected.
                    </p>
                    <p className="text-[11px] text-slate-400">
                      You can copy the generated prompt blueprint directly into local ComfyUI, AUTOMATIC1111, or SDXL local server.
                    </p>
                  </div>

                  <div className="space-y-2 text-xs">
                    <div className="flex justify-between py-1 border-b border-slate-800">
                      <span className="text-slate-400">Target Model:</span>
                      <span className="font-mono text-white">SDXL Base 1.0 (Local)</span>
                    </div>
                    <div className="flex justify-between py-1 border-b border-slate-800">
                      <span className="text-slate-400">Sampler:</span>
                      <span className="font-mono text-white">DPM++ 2M Karras</span>
                    </div>
                    <div className="flex justify-between py-1 border-b border-slate-800">
                      <span className="text-slate-400">CFG Scale:</span>
                      <span className="font-mono text-white">7.0</span>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          </div>
        )}

        {/* Tab 2: Video Script Generator */}
        {activeTab === "video" && (
          <Card>
            <CardHeader>
              <CardTitle className="text-base text-white">Vertical Video Script Formulation</CardTitle>
              <CardDescription>
                Short-form TikTok / Reels / Shorts 60-second retention-engineered scripts
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="p-4 rounded-lg bg-navy-950 border border-slate-800 space-y-3 font-mono text-xs">
                <div className="text-blue-400 font-bold">[00:00 - 00:03] THE HOOK (Visual: Red flashing alert on dark terminal)</div>
                <p className="text-slate-300">"90% of AI marketing teams are one audit away from a total company shutdown."</p>

                <div className="text-blue-400 font-bold">[00:03 - 00:20] THE PROBLEM</div>
                <p className="text-slate-300">"Everyone talks about prompt speed. Nobody talks about hash chains or business isolation. If your agents publish unverified content, you carry 100% of the liability."</p>

                <div className="text-blue-400 font-bold">[00:20 - 00:45] THE SOLUTION</div>
                <p className="text-slate-300">"Here is how 8 specialized agents work together with cryptographic audit logging and mandatory human publishing signoffs."</p>

                <div className="text-blue-400 font-bold">[00:45 - 00:60] CALL TO ACTION</div>
                <p className="text-slate-300">"Self-host your own sovereign team. Link in bio to access the v2 open-source repo."</p>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Tab 3: Asset Library */}
        {activeTab === "assets" && (
          <Card>
            <CardHeader>
              <CardTitle className="text-base text-white">Verified Brand Asset Vault</CardTitle>
              <CardDescription>Hex codes, logos, and approved typography</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-xs">
                <div className="p-4 rounded-lg border border-slate-800 bg-navy-950">
                  <div className="h-10 w-full rounded bg-[#050811] border border-slate-700 mb-2" />
                  <div className="font-semibold text-white">Primary Canvas</div>
                  <div className="text-slate-400 font-mono">#050811 (Dark Navy 950)</div>
                </div>
                <div className="p-4 rounded-lg border border-slate-800 bg-navy-950">
                  <div className="h-10 w-full rounded bg-[#3B82F6] mb-2" />
                  <div className="font-semibold text-white">Accent Electric Blue</div>
                  <div className="text-slate-400 font-mono">#3B82F6 (Primary 500)</div>
                </div>
                <div className="p-4 rounded-lg border border-slate-800 bg-navy-950">
                  <div className="h-10 w-full rounded bg-[#06B6D4] mb-2" />
                  <div className="font-semibold text-white">Cyber Cyan</div>
                  <div className="text-slate-400 font-mono">#06B6D4 (Telemetry)</div>
                </div>
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </AppLayout>
  );
}

