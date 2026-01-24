"use client";

import { useRouter } from "next/navigation";
import { ArrowRight, Sparkles, Brain, TrendingUp, Shield } from "lucide-react";

export default function LandingPage() {
  const router = useRouter();

  const features = [
    {
      icon: <Brain className="w-6 h-6" />,
      title: "MBB-Grade Analysis",
      description: "Strategic thinking powered by McKinsey, BCG, and Bain frameworks"
    },
    {
      icon: <Sparkles className="w-6 h-6" />,
      title: "AI-Powered Insights",
      description: "Advanced LLM models analyze companies with enterprise-grade depth"
    },
    {
      icon: <TrendingUp className="w-6 h-6" />,
      title: "Dynamic Prompts",
      description: "Intent analyzer generates tailored prompts for each analysis"
    },
    {
      icon: <Shield className="w-6 h-6" />,
      title: "Professional Reports",
      description: "Download PDF reports and PowerPoint pitch decks instantly"
    }
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 via-purple-50 to-indigo-50">
      {/* Navigation */}
      <nav className="border-b border-gray-200 bg-white/80 backdrop-blur-sm">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-10 h-10 bg-gradient-to-br from-purple-600 to-indigo-600 rounded-xl flex items-center justify-center text-white font-bold text-lg">
              S
            </div>
            <span className="text-xl font-bold text-gray-900">Stratagem AI</span>
          </div>
          <button
            onClick={() => router.push("/chat")}
            className="px-6 py-2 bg-gradient-to-r from-purple-600 to-indigo-600 text-white rounded-xl font-semibold hover:shadow-lg transition-all"
          >
            Get Started
          </button>
        </div>
      </nav>

      {/* Hero Section */}
      <div className="max-w-7xl mx-auto px-6 py-20">
        <div className="text-center space-y-8">
          {/* Badge */}
          <div className="inline-flex items-center gap-2 px-4 py-2 bg-white border border-purple-200 rounded-full text-sm">
            <Sparkles className="w-4 h-4 text-purple-600" />
            <span className="text-gray-700">Enterprise-Grade Strategy Research Platform</span>
          </div>

          {/* Heading */}
          <h1 className="text-6xl font-bold text-gray-900 leading-tight">
            Strategic Intelligence
            <br />
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-purple-600 to-indigo-600">
              Powered by AI
            </span>
          </h1>

          {/* Subheading */}
          <p className="text-xl text-gray-600 max-w-2xl mx-auto leading-relaxed">
            Get MBB-level strategic analysis in minutes. Our AI platform uses frameworks from
            McKinsey, BCG, and Bain to deliver enterprise-grade insights.
          </p>

          {/* CTA Buttons */}
          <div className="flex items-center justify-center gap-4 pt-4">
            <button
              onClick={() => router.push("/chat")}
              className="group px-8 py-4 bg-gradient-to-r from-purple-600 to-indigo-600 text-white rounded-2xl font-semibold hover:shadow-xl transition-all flex items-center gap-2"
            >
              Start Analysis
              <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
            </button>
            <button className="px-8 py-4 bg-white border border-gray-300 text-gray-700 rounded-2xl font-semibold hover:border-purple-300 hover:shadow-md transition-all">
              View Demo
            </button>
          </div>
        </div>

        {/* Features Grid */}
        <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6 mt-24">
          {features.map((feature, idx) => (
            <div
              key={idx}
              className="p-6 bg-white border border-gray-200 rounded-3xl hover:border-purple-300 hover:shadow-lg transition-all group"
            >
              <div className="w-12 h-12 bg-gradient-to-br from-purple-100 to-indigo-100 rounded-2xl flex items-center justify-center text-purple-600 mb-4 group-hover:scale-110 transition-transform">
                {feature.icon}
              </div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">
                {feature.title}
              </h3>
              <p className="text-sm text-gray-600 leading-relaxed">
                {feature.description}
              </p>
            </div>
          ))}
        </div>

        {/* Frameworks Section */}
        <div className="mt-24 text-center">
          <h2 className="text-3xl font-bold text-gray-900 mb-4">
            Strategic Frameworks
          </h2>
          <p className="text-gray-600 mb-12 max-w-2xl mx-auto">
            Our AI applies proven consulting frameworks to deliver structured, actionable insights
          </p>

          <div className="grid md:grid-cols-3 lg:grid-cols-4 gap-4">
            {[
              "Porter's 5 Forces",
              "Value Chain Analysis",
              "DuPont ROE Analysis",
              "SWOT Analysis",
              "Ansoff Matrix",
              "PESTEL Analysis",
              "VRIO Framework",
              "McKinsey 7S"
            ].map((framework, idx) => (
              <div
                key={idx}
                className="px-6 py-4 bg-white border border-gray-200 rounded-2xl hover:border-purple-300 hover:shadow-md transition-all"
              >
                <span className="text-sm font-medium text-gray-700">
                  {framework}
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* CTA Section */}
        <div className="mt-24 p-12 bg-gradient-to-r from-purple-600 to-indigo-600 rounded-3xl text-center text-white">
          <h2 className="text-4xl font-bold mb-4">
            Ready to get started?
          </h2>
          <p className="text-xl mb-8 opacity-90">
            Start your first strategic analysis in seconds
          </p>
          <button
            onClick={() => router.push("/chat")}
            className="px-10 py-4 bg-white text-purple-600 rounded-2xl font-semibold hover:shadow-xl transition-all"
          >
            Launch Platform
          </button>
        </div>
      </div>

      {/* Footer */}
      <footer className="border-t border-gray-200 bg-white/80 backdrop-blur-sm mt-20">
        <div className="max-w-7xl mx-auto px-6 py-8 text-center text-gray-600 text-sm">
          <p>© 2026 Stratagem AI. Enterprise-Grade Strategy Research Platform.</p>
        </div>
      </footer>
    </div>
  );
}
