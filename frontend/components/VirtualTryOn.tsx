import React, { useState, useRef } from 'react';

interface ClothingItem {
  item_id: string;
  name: string;
  image_url: string;
  price_inr: number;
  brand: string;
}

interface VirtualTryOnProps {
  item: ClothingItem;
  userId: string;
  onClose: () => void;
}

const VirtualTryOn: React.FC<VirtualTryOnProps> = ({ item, userId, onClose }) => {
  const [userImage, setUserImage] = useState<string | null>(null);
  const [generatedImage, setGeneratedImage] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [jobId, setJobId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Handle file upload
  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = (event) => {
        setUserImage(event.target?.result as string);
      };
      reader.readAsDataURL(file);
    }
  };

  // Generate try-on
  const handleGenerate = async () => {
    if (!fileInputRef.current?.files?.[0]) {
      setError('Please upload your photo first');
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      const formData = new FormData();
      formData.append('user_id', userId);
      formData.append('item_id', item.item_id);
      formData.append('file', fileInputRef.current.files[0]);

      const response = await fetch('/api/v1/tryon/generate', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error('Failed to initiate try-on');
      }

      const data = await response.json();
      setJobId(data.job_id);

      // Poll for results
      pollForResult(data.job_id);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to generate try-on');
      setIsLoading(false);
    }
  };

  // Poll for job result
  const pollForResult = async (currentJobId: string) => {
    const maxAttempts = 60; // 60 attempts * 2s = 2 minutes
    let attempts = 0;

    const poll = async () => {
      try {
        const response = await fetch(`/api/v1/tryon/result/${currentJobId}`);
        if (!response.ok) {
          throw new Error('Failed to check status');
        }

        const data = await response.json();

        if (data.status === 'completed') {
          setGeneratedImage(data.generated_image);
          setIsLoading(false);
        } else if (data.status === 'failed') {
          setError(data.error_message || 'Try-on failed');
          setIsLoading(false);
        } else if (attempts < maxAttempts) {
          attempts++;
          setTimeout(poll, 2000);
        } else {
          setError('Try-on timed out. Please try again.');
          setIsLoading(false);
        }
      } catch (err) {
        setError('Failed to check try-on status');
        setIsLoading(false);
      }
    };

    poll();
  };

  // Download generated image
  const handleDownload = () => {
    if (generatedImage) {
      const link = document.createElement('a');
      link.href = generatedImage;
      link.download = `fitsaathi-tryon-${item.item_id}.jpg`;
      link.click();
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-80 flex items-center justify-center z-50 p-4">
      <div className="bg-gradient-to-br from-slate-800 to-slate-900 rounded-2xl p-6 max-w-2xl w-full shadow-2xl border border-amber-500/30">
        {/* Header */}
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-2xl font-bold text-amber-400 font-serif">
            Virtual Try-On
          </h2>
          <button
            onClick={onClose}
            className="w-10 h-10 rounded-full bg-white/10 hover:bg-white/20 text-white flex items-center justify-center transition-all"
          >
            ✕
          </button>
        </div>

        {/* Item Info */}
        <div className="flex items-center gap-4 mb-6 p-4 bg-white/5 rounded-xl">
          <img
            src={item.image_url}
            alt={item.name}
            className="w-20 h-20 object-cover rounded-lg"
          />
          <div>
            <p className="text-sm text-amber-300 font-medium">{item.brand}</p>
            <h3 className="text-white font-semibold">{item.name}</h3>
            <p className="text-amber-400 font-bold">₹{item.price_inr}</p>
          </div>
        </div>

        {/* Error */}
        {error && (
          <div className="mb-4 p-3 bg-red-500/20 border border-red-500/50 rounded-lg text-red-300">
            {error}
          </div>
        )}

        {/* Upload/Preview Section */}
        <div className="mb-6">
          {!userImage ? (
            <div
              onClick={() => fileInputRef.current?.click()}
              className="border-2 border-dashed border-amber-500/50 rounded-xl p-12 text-center cursor-pointer hover:border-amber-500 transition-colors"
            >
              <div className="text-6xl mb-4">📸</div>
              <p className="text-white font-medium mb-2">Upload Your Photo</p>
              <p className="text-slate-400 text-sm">
                JPG, PNG, or WebP (Max 10MB)
              </p>
            </div>
          ) : (
            <div className="relative rounded-xl overflow-hidden">
              {/* User's photo */}
              <img
                src={userImage}
                alt="Your photo"
                className="w-full object-cover max-h-[400px]"
              />

              {/* Generated try-on overlay */}
              {generatedImage && (
                <img
                  src={generatedImage}
                  alt="Try-on result"
                  className="absolute inset-0 w-full h-full object-cover"
                />
              )}

              {/* Loading indicator */}
              {isLoading && (
                <div className="absolute inset-0 bg-black/60 flex items-center justify-center">
                  <div className="text-center">
                    <div className="w-12 h-12 border-4 border-amber-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
                    <p className="text-white">Generating Your Virtual Try-On...</p>
                  </div>
                </div>
              )}
            </div>
          )}

          <input
            ref={fileInputRef}
            type="file"
            accept="image/*"
            onChange={handleFileChange}
            className="hidden"
          />
        </div>

        {/* Controls */}
        <div className="flex gap-3">
          {!generatedImage ? (
            <button
              onClick={handleGenerate}
              disabled={!userImage || isLoading}
              className="flex-1 bg-gradient-to-r from-amber-600 to-amber-500 text-white py-3 rounded-xl font-semibold hover:from-amber-500 hover:to-amber-400 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isLoading ? 'Generating...' : 'Generate Try-On'}
            </button>
          ) : (
            <>
              <button
                onClick={() => {
                  setGeneratedImage(null);
                  setUserImage(null);
                  setJobId(null);
                  setError(null);
                  if (fileInputRef.current) {
                    fileInputRef.current.value = '';
                  }
                }}
                className="flex-1 bg-white/10 text-white py-3 rounded-xl font-semibold hover:bg-white/20 transition-all"
              >
                Try Again
              </button>
              <button
                onClick={handleDownload}
                className="flex-1 bg-gradient-to-r from-emerald-600 to-emerald-500 text-white py-3 rounded-xl font-semibold hover:from-emerald-500 hover:to-emerald-400 transition-all"
              >
                Download Result
              </button>
            </>
          )}
        </div>
      </div>
    </div>
  );
};

export default VirtualTryOn;
