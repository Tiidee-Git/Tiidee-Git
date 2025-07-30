import { useState, useEffect } from 'react'
import { Button } from '@/components/ui/button.jsx'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card.jsx'
import { Textarea } from '@/components/ui/textarea.jsx'
import { Input } from '@/components/ui/input.jsx'
import { Label } from '@/components/ui/label.jsx'
import { Badge } from '@/components/ui/badge.jsx'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs.jsx'
import { Upload, Video, Mic, Download, Play, Wifi, WifiOff, Save, FolderOpen, Languages, Globe } from 'lucide-react'
import { useOffline } from './hooks/useOffline.js'
import { DzongkhaInput } from './components/DzongkhaInput.jsx'
import snowLionLogo from './assets/snow-lion-logo.jpg'
import './App.css'

function App() {
  const [script, setScript] = useState('')
  const [language, setLanguage] = useState('en')
  const [voiceFile, setVoiceFile] = useState(null)
  const [isGenerating, setIsGenerating] = useState(false)
  const [generatedVideo, setGeneratedVideo] = useState(null)
  const [drafts, setDrafts] = useState([])
  const [currentDraft, setCurrentDraft] = useState(null)
  const [videoTitle, setVideoTitle] = useState('')
  const [dzongkhaCapabilities, setDzongkhaCapabilities] = useState(null)
  
  const { isOnline, saveOfflineData, getOfflineData, addToOfflineQueue } = useOffline()

  useEffect(() => {
    // Load drafts on startup
    loadDrafts()
    
    // Load Dzongkha capabilities
    loadDzongkhaCapabilities()
    
    // Load any saved draft from localStorage
    const savedDraft = getOfflineData('currentDraft')
    if (savedDraft) {
      setScript(savedDraft.script || '')
      setVideoTitle(savedDraft.title || '')
      setLanguage(savedDraft.language || 'en')
    }
  }, [])

  useEffect(() => {
    // Auto-save current work
    if (script || videoTitle) {
      saveOfflineData('currentDraft', {
        script,
        title: videoTitle,
        language,
        timestamp: new Date().toISOString()
      })
    }
  }, [script, videoTitle, language])

  const loadDzongkhaCapabilities = async () => {
    try {
      const response = await fetch('/api/dzongkha/capabilities')
      if (response.ok) {
        const data = await response.json()
        setDzongkhaCapabilities(data.capabilities)
      }
    } catch (error) {
      console.error('Failed to load Dzongkha capabilities:', error)
    }
  }

  const loadDrafts = async () => {
    try {
      const endpoint = isOnline ? '/api/offline/list-drafts' : null
      
      if (endpoint) {
        const response = await fetch(endpoint)
        if (response.ok) {
          const data = await response.json()
          setDrafts(data.drafts || [])
        }
      } else {
        // Load from localStorage when offline
        const offlineDrafts = getOfflineData('drafts') || []
        setDrafts(offlineDrafts)
      }
    } catch (error) {
      console.error('Failed to load drafts:', error)
      // Fallback to localStorage
      const offlineDrafts = getOfflineData('drafts') || []
      setDrafts(offlineDrafts)
    }
  }

  const handleVoiceUpload = (event) => {
    const file = event.target.files[0]
    setVoiceFile(file)
  }

  const handleSaveDraft = async () => {
    if (!script.trim() && !videoTitle.trim()) {
      alert('Please enter a title or script to save')
      return
    }

    const draftData = {
      title: videoTitle || 'Untitled Draft',
      script: script,
      language: language,
      voice_id: 'default',
      settings: {},
      created_at: new Date().toISOString()
    }

    try {
      if (isOnline) {
        const response = await fetch('/api/offline/save-draft', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(draftData)
        })

        if (response.ok) {
          const result = await response.json()
          alert('Draft saved successfully!')
          loadDrafts()
        } else {
          throw new Error('Failed to save draft online')
        }
      } else {
        // Save offline
        const offlineDrafts = getOfflineData('drafts') || []
        const newDraft = {
          ...draftData,
          id: `offline_${Date.now()}`
        }
        offlineDrafts.push(newDraft)
        saveOfflineData('drafts', offlineDrafts)
        setDrafts(offlineDrafts)
        alert('Draft saved offline!')
      }
    } catch (error) {
      console.error('Failed to save draft:', error)
      // Fallback to offline save
      const offlineDrafts = getOfflineData('drafts') || []
      const newDraft = {
        ...draftData,
        id: `offline_${Date.now()}`
      }
      offlineDrafts.push(newDraft)
      saveOfflineData('drafts', offlineDrafts)
      setDrafts(offlineDrafts)
      alert('Draft saved offline!')
    }
  }

  const handleLoadDraft = (draft) => {
    setScript(draft.script || '')
    setVideoTitle(draft.title || '')
    setLanguage(draft.language || 'en')
    setCurrentDraft(draft)
  }

  const handleGenerateVideo = async () => {
    if (!script.trim()) {
      alert('Please enter a script')
      return
    }

    setIsGenerating(true)
    
    try {
      // Determine which endpoint to use based on connection and language
      let endpoint = '/api/generate-video'
      
      if (language === 'dz') {
        // Use Dzongkha-specific video generation
        endpoint = '/api/dzongkha/generate-video-with-dzongkha'
      } else if (!isOnline) {
        endpoint = '/api/offline/generate-video-offline'
      }
      
      // First upload voice sample if provided
      let voiceId = 'default'
      if (voiceFile && isOnline) {
        const formData = new FormData()
        formData.append('voice_file', voiceFile)
        
        const voiceResponse = await fetch('/api/upload-voice-sample', {
          method: 'POST',
          body: formData
        })
        
        if (voiceResponse.ok) {
          const voiceResult = await voiceResponse.json()
          voiceId = voiceResult.voice_id
        }
      }

      // Generate video
      const videoData = {
        script: script,
        dzongkha_script: language === 'dz' ? script : '',
        english_script: language === 'en' ? script : '',
        voice_id: voiceId,
        voice_preference: language === 'dz' ? 'dzongkha' : 'default',
        title: videoTitle || 'Generated Video',
        style: language === 'dz' ? 'traditional' : 'business',
        language: language
      }

      if (isOnline) {
        const response = await fetch(endpoint, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(videoData)
        })

        if (response.ok) {
          const result = await response.json()
          setGeneratedVideo(result)
        } else {
          throw new Error('Video generation failed')
        }
      } else {
        // Queue for offline processing
        addToOfflineQueue(async () => {
          const response = await fetch('/api/offline/generate-video-offline', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(videoData)
          })
          
          if (response.ok) {
            const result = await response.json()
            setGeneratedVideo(result)
          }
        })

        // Show offline message
        setGeneratedVideo({
          job_id: `offline_${Date.now()}`,
          status: 'queued',
          message: `Video queued for generation. Will process when online.`,
          offline: true,
          language: language
        })
      }
    } catch (error) {
      console.error('Error:', error)
      alert('Failed to generate video. Please try again.')
    } finally {
      setIsGenerating(false)
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 p-4">
      <div className="max-w-6xl mx-auto">
        {/* Header with Connection Status */}
        <div className="text-center mb-8">
          <div className="flex items-center justify-center gap-4 mb-4">
            <img 
              src={snowLionLogo} 
              alt="Snow Lion" 
              className="w-16 h-16 rounded-full object-cover border-2 border-blue-200 shadow-lg"
            />
            <div>
              <h1 className="text-4xl font-bold text-gray-900">
                Dawa Present
              </h1>
              <div className="flex items-center justify-center gap-2 mt-2">
                {isOnline ? (
                  <Badge variant="default" className="bg-green-500">
                    <Wifi className="w-3 h-3 mr-1" />
                    Online
                  </Badge>
                ) : (
                  <Badge variant="secondary" className="bg-orange-500 text-white">
                    <WifiOff className="w-3 h-3 mr-1" />
                    Offline Mode
                  </Badge>
                )}
                {dzongkhaCapabilities && (
                  <Badge variant="outline" className="bg-purple-50 text-purple-700 border-purple-200">
                    <Languages className="w-3 h-3 mr-1" />
                    རྫོང་ཁ Enabled
                  </Badge>
                )}
              </div>
            </div>
          </div>
          <p className="text-lg text-gray-600">
            AI-Powered Video Generation from Text & Voice
          </p>
          <p className="text-sm text-gray-500 mt-1">
            Powered by the Spirit of the Snow Lion • Now with Dzongkha Support
          </p>
          {!isOnline && (
            <p className="text-sm text-orange-600 mt-2">
              Working offline - your content will sync when connection is restored
            </p>
          )}
        </div>

        {/* Main Content */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Input Section */}
          <div className="lg:col-span-2 space-y-6">
            {/* Language Selection and Basic Input */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Video className="w-5 h-5" />
                  Create Your Video
                </CardTitle>
                <CardDescription>
                  Enter your script in English or Dzongkha and optionally upload your voice sample
                </CardDescription>
              </CardHeader>
              <CardContent>
                <Tabs defaultValue="basic" className="w-full">
                  <TabsList className="grid w-full grid-cols-2">
                    <TabsTrigger value="basic">Basic Input</TabsTrigger>
                    <TabsTrigger value="dzongkha">
                      <Languages className="w-4 h-4 mr-1" />
                      Dzongkha Tools
                    </TabsTrigger>
                  </TabsList>
                  
                  <TabsContent value="basic" className="space-y-4 mt-4">
                    {/* Video Title */}
                    <div>
                      <Label htmlFor="title">Video Title</Label>
                      <Input
                        id="title"
                        placeholder="Enter video title..."
                        value={videoTitle}
                        onChange={(e) => setVideoTitle(e.target.value)}
                        className="mt-1"
                      />
                    </div>

                    {/* Language Selection */}
                    <div>
                      <Label htmlFor="language">Script Language</Label>
                      <div className="flex gap-2 mt-1">
                        <Button
                          variant={language === 'en' ? 'default' : 'outline'}
                          size="sm"
                          onClick={() => setLanguage('en')}
                        >
                          <Globe className="w-4 h-4 mr-1" />
                          English
                        </Button>
                        <Button
                          variant={language === 'dz' ? 'default' : 'outline'}
                          size="sm"
                          onClick={() => setLanguage('dz')}
                        >
                          <Languages className="w-4 h-4 mr-1" />
                          རྫོང་ཁ
                        </Button>
                      </div>
                    </div>

                    {/* Script Input */}
                    <div>
                      <Label htmlFor="script">
                        {language === 'dz' ? 'Dzongkha Script' : 'English Script'}
                      </Label>
                      <Textarea
                        id="script"
                        placeholder={
                          language === 'dz' 
                            ? "རྫོང་ཁའི་ཡིག་ཆ་འདིར་འབྲི་རོགས།..." 
                            : "Enter your video script here..."
                        }
                        value={script}
                        onChange={(e) => setScript(e.target.value)}
                        rows={8}
                        className={`mt-1 ${language === 'dz' ? 'font-mono' : ''}`}
                        style={language === 'dz' ? { direction: 'ltr', unicodeBidi: 'embed' } : {}}
                      />
                    </div>

                    {/* Voice Upload */}
                    <div>
                      <Label htmlFor="voice-upload">Voice Sample (Optional)</Label>
                      <div className="mt-1">
                        <Input
                          id="voice-upload"
                          type="file"
                          accept="audio/*"
                          onChange={handleVoiceUpload}
                          disabled={!isOnline}
                          className="file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
                        />
                        {voiceFile && (
                          <p className="text-sm text-green-600 mt-1">
                            ✓ Voice sample uploaded: {voiceFile.name}
                          </p>
                        )}
                        {!isOnline && (
                          <p className="text-sm text-orange-600 mt-1">
                            Voice upload requires internet connection
                          </p>
                        )}
                      </div>
                    </div>

                    {/* Action Buttons */}
                    <div className="flex gap-2">
                      <Button 
                        onClick={handleGenerateVideo}
                        disabled={isGenerating || !script.trim()}
                        className="flex-1"
                        size="lg"
                      >
                        {isGenerating ? (
                          <>
                            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                            Generating Video...
                          </>
                        ) : (
                          <>
                            <Play className="w-4 h-4 mr-2" />
                            Generate Video {language === 'dz' ? '(རྫོང་ཁ)' : ''} {!isOnline && '(Offline)'}
                          </>
                        )}
                      </Button>
                      
                      <Button 
                        onClick={handleSaveDraft}
                        variant="outline"
                        size="lg"
                      >
                        <Save className="w-4 h-4 mr-2" />
                        Save Draft
                      </Button>
                    </div>
                  </TabsContent>
                  
                  <TabsContent value="dzongkha" className="mt-4">
                    <DzongkhaInput
                      onScriptChange={setScript}
                      onLanguageChange={setLanguage}
                      initialScript={script}
                      initialLanguage={language}
                    />
                  </TabsContent>
                </Tabs>
              </CardContent>
            </Card>
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            {/* Output Section */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Download className="w-5 h-5" />
                  Generated Video
                </CardTitle>
                <CardDescription>
                  Preview and download your video
                </CardDescription>
              </CardHeader>
              <CardContent>
                {generatedVideo ? (
                  <div className="space-y-4">
                    <div className="bg-gray-100 rounded-lg p-4 text-center">
                      <Video className="w-16 h-16 mx-auto text-gray-400 mb-2" />
                      <p className="text-sm text-gray-600">
                        {generatedVideo.offline ? 'Video queued for offline processing' : 'Video generated successfully!'}
                      </p>
                      <p className="text-xs text-gray-500">Job ID: {generatedVideo.job_id}</p>
                      {generatedVideo.language === 'dz' && (
                        <Badge variant="outline" className="mt-2">
                          <Languages className="w-3 h-3 mr-1" />
                          Dzongkha Video
                        </Badge>
                      )}
                    </div>
                    
                    {!generatedVideo.offline && (
                      <Button asChild className="w-full">
                        <a href={generatedVideo.video_url} download>
                          <Download className="w-4 h-4 mr-2" />
                          Download Video
                        </a>
                      </Button>
                    )}
                  </div>
                ) : (
                  <div className="bg-gray-50 rounded-lg p-8 text-center">
                    <Video className="w-16 h-16 mx-auto text-gray-300 mb-4" />
                    <p className="text-gray-500">
                      Your generated video will appear here
                    </p>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Drafts Section */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <FolderOpen className="w-5 h-5" />
                  Saved Drafts
                </CardTitle>
                <CardDescription>
                  Load your saved drafts
                </CardDescription>
              </CardHeader>
              <CardContent>
                {drafts.length > 0 ? (
                  <div className="space-y-2 max-h-60 overflow-y-auto">
                    {drafts.map((draft) => (
                      <div 
                        key={draft.id}
                        className="p-3 border rounded-lg cursor-pointer hover:bg-gray-50 transition-colors"
                        onClick={() => handleLoadDraft(draft)}
                      >
                        <div className="flex items-center justify-between">
                          <p className="font-medium text-sm">{draft.title}</p>
                          {draft.language === 'dz' && (
                            <Badge variant="outline" className="text-xs">
                              རྫོང་ཁ
                            </Badge>
                          )}
                        </div>
                        <p className="text-xs text-gray-500">
                          {new Date(draft.created_at || draft.updated_at).toLocaleDateString()}
                        </p>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-gray-500 text-sm text-center py-4">
                    No drafts saved yet
                  </p>
                )}
              </CardContent>
            </Card>
          </div>
        </div>

        {/* Features Section */}
        <div className="mt-12 grid grid-cols-1 md:grid-cols-4 gap-6">
          <Card>
            <CardContent className="pt-6">
              <div className="text-center">
                <Mic className="w-8 h-8 mx-auto text-blue-600 mb-2" />
                <h3 className="font-semibold mb-1">Voice Cloning</h3>
                <p className="text-sm text-gray-600">
                  Upload your voice sample and generate videos in your own voice
                </p>
                {!isOnline && (
                  <Badge variant="secondary" className="mt-2 text-xs">
                    Requires Internet
                  </Badge>
                )}
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="pt-6">
              <div className="text-center">
                <Video className="w-8 h-8 mx-auto text-green-600 mb-2" />
                <h3 className="font-semibold mb-1">Offline Generation</h3>
                <p className="text-sm text-gray-600">
                  Create videos even without internet using local AI processing
                </p>
                <Badge variant="default" className="mt-2 text-xs bg-green-500">
                  Works Offline
                </Badge>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="pt-6">
              <div className="text-center">
                <Languages className="w-8 h-8 mx-auto text-purple-600 mb-2" />
                <h3 className="font-semibold mb-1">Dzongkha Support</h3>
                <p className="text-sm text-gray-600">
                  Full support for Dzongkha script, speech recognition, and TTS
                </p>
                <Badge variant="default" className="mt-2 text-xs bg-purple-500">
                  རྫོང་ཁ Ready
                </Badge>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="pt-6">
              <div className="text-center">
                <Upload className="w-8 h-8 mx-auto text-orange-600 mb-2" />
                <h3 className="font-semibold mb-1">Auto Sync</h3>
                <p className="text-sm text-gray-600">
                  Your work syncs automatically when connection is restored
                </p>
                <Badge variant="default" className="mt-2 text-xs bg-orange-500">
                  Smart Sync
                </Badge>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}

export default App
