'use client';

import axios from 'axios';
import { useState } from 'react';
import { backend_url } from '@/config/config';

export default function Page() {
  const [file, setFile] = useState<File | null>(null);
  const [fileType, setFileType] = useState<string>('image');
  const [description, setDescription] = useState<string>('');
  const [message, setMessage] = useState<string>('');
  const [uploading, setUploading] = useState(false);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      setFile(e.target.files[0]);
    }
  };

  const handleUpload = async () => {
    if (!file) {
      setMessage('⚠️ Please select a file first.');
      return;
    }

    const formData = new FormData();
    formData.append('file', file);
    formData.append('file_type', fileType);

    if (['image', 'audio', 'video'].includes(fileType)) {
      formData.append('description', description);
    } else {
      formData.append('description', '');
    }

    try {
      setUploading(true);
      const token = localStorage.getItem('org_jwt');
      const res = await axios.post(`${backend_url}/api/v1/uploads/upload-file/`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
          Authorization: `Bearer ${token}`,
        },
      });

      setMessage(`✅ ${res.data.message}: ${res.data.filename}`);
    } catch {
      setMessage('❌ Something went wrong while uploading the file.');
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="flex min-h-screen h-full items-center justify-center px-4">
      <div className="bg-white shadow-xl rounded-2xl p-8 w-full max-w-md transition hover:shadow-2xl">
        <h2 className="text-2xl font-semibold text-center text-gray-800 mb-6">Upload File</h2>

        {/* Dropdown */}
        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-600 mb-1">Select File Type</label>
          <select
            value={fileType}
            onChange={(e) => setFileType(e.target.value)}
            className="w-full rounded-lg border border-gray-300 px-3 py-2 text-gray-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="image">Image</option>
            <option value="pdf">PDF / Docs</option>
            <option value="audio">Audio</option>
            <option value="video">Video</option>
          </select>
        </div>

        {/* Description input for image, audio, video */}
        {['image', 'audio', 'video'].includes(fileType) && (
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-600 mb-1">
              {fileType.charAt(0).toUpperCase() + fileType.slice(1)} Description
            </label>
            <input
              type="text"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder={`Enter a short description for the ${fileType}...`}
              className="w-full rounded-lg border border-gray-300 px-3 py-2 text-gray-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
        )}

        {/* File input */}
        <div className="mb-4">
          <input
            type="file"
            accept={
              fileType === 'image'
                ? 'image/*'
                : fileType === 'audio'
                  ? 'audio/*'
                  : fileType === 'video'
                    ? 'video/*'
                    : '.pdf,.doc,.docx'
            }
            onChange={handleFileChange}
            className="w-full text-sm text-gray-600 border border-gray-300 rounded-lg p-2 cursor-pointer focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        {/* Upload button */}
        <button
          onClick={handleUpload}
          className={`w-full bg-blue-600 text-white font-medium py-2 rounded-xl hover:bg-blue-700 active:scale-[0.98] transition-all duration-150 cursor-pointer ${uploading ? 'opacity-60 cursor-not-allowed' : ''}`}
          disabled={uploading}
        >
          {uploading ? (
            <span className="flex items-center justify-center">
              <svg
                className="animate-spin h-5 w-5 mr-2 text-white"
                xmlns="http://www.w3.org/2000/svg"
                fill="none"
                viewBox="0 0 24 24"
              >
                <circle
                  className="opacity-25"
                  cx="12"
                  cy="12"
                  r="10"
                  stroke="currentColor"
                  strokeWidth="4"
                ></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z"></path>
              </svg>
              Uploading...
            </span>
          ) : (
            'Upload'
          )}
        </button>

        {/* Message */}
        {message && <p className="mt-4 text-center text-sm font-medium text-gray-700">{message}</p>}
      </div>
    </div>
  );
}
