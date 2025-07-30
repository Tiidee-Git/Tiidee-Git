import { useState, useEffect } from 'react'
import { Button } from '@/components/ui/button.jsx'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card.jsx'
import { Textarea } from '@/components/ui/textarea.jsx'
import { Input } from '@/components/ui/input.jsx'
import { Label } from '@/components/ui/label.jsx'
import { Badge } from '@/components/ui/badge.jsx'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select.jsx'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs.jsx'
import { 
  Languages, 
  Mic, 
  MicOff, 
  Volume2, 
  VolumeX, 
  CheckCircle, 
  AlertCircle, 
  Globe,
  FileText,
  Play,
  Square
} from 'lucide-react'

export function DzongkhaInput({ 
  onScriptChange, 
  onLanguageChange, 
  initialScript = '', 
  initialLanguage = 'en' 
}) {
  const [script, setScript] = useState(initialScript)
  const [language, setLanguage] = useState(initialLanguage)
  const [dzongkhaText, setDzongkhaText] = useState('')
  const [englishText, setEnglishText] = useState('')
  const [isRecording, setIsRecording] = useState(false)
  const [audioBlob, setAudioBlob] = useState(null)
  const [transcription, setTranscription] = useState(null)
  const [validation, setValidation] = useState(null)
  const [translation, setTranslation] = useState(null)
  const [capabilities, setCapabilities] = useState(null)
  const [isLoading, setIsLoading] = useState(false)

  useEffect(() => {
    // Load Dzongkha capabilities on component mount
    loadCapabilities()
  }, [])

  useEffect(() => {
    // Update parent component when script or language changes
    onScriptChange(script)
    onLanguageChange(language)
  }, [script, language, onScriptChange, onLanguageChange])

  const loadCapabilities = async () => {
    try {
      const response = await fetch('/api/dzongkha/capabilities')
      if (response.ok) {
        const data = await response.json()
        setCapabilities(data.capabilities)
      }
    } catch (error) {
      console.error('Failed to load Dzongkha capabilities:', error)
    }
  }

  const handleLanguageChange = (newLanguage) => {
    setLanguage(newLanguage)
    
    if (newLanguage === 'dz') {
      setScript(dzongkhaText)
    } else {
      setScript(englishText)
    }
  }

  const handleTextChange = (text) => {
    if (language === 'dz') {
      setDzongkhaText(text)
      validateDzongkhaText(text)
    } else {
      setEnglishText(text)
    }
    setScript(text)
  }

  const validateDzongkhaText = async (text) => {
    if (!text.trim()) {
      setValidation(null)
      return
    }

    try {
      const response = await fetch('/api/dzongkha/validate-text', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text })
      })

      if (response.ok) {
        const data = await response.json()
        setValidation(data.validation)
      }
    } catch (error) {
      console.error('Text validation failed:', error)
    }
  }

  const translateText = async (text, sourceLang, targetLang) => {
    setIsLoading(true)
    try {
      const response = await fetch('/api/dzongkha/translate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          text,
          source_lang: sourceLang,
          target_lang: targetLang
        })
      })

      if (response.ok) {
        const data = await response.json()
        setTranslation(data.translation)
        
        // Auto-fill the target language text
        if (targetLang === 'dz') {
          setDzongkhaText(data.translation.translated_text)
        } else {
          setEnglishText(data.translation.translated_text)
        }
      }
    } catch (error) {
      console.error('Translation failed:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      const mediaRecorder = new MediaRecorder(stream)
      const chunks = []

      mediaRecorder.ondataavailable = (event) => {
        chunks.push(event.data)
      }

      mediaRecorder.onstop = () => {
        const blob = new Blob(chunks, { type: 'audio/wav' })
        setAudioBlob(blob)
        transcribeAudio(blob)
        
        // Stop all tracks
        stream.getTracks().forEach(track => track.stop())
      }

      mediaRecorder.start()
      setIsRecording(true)

      // Auto-stop after 30 seconds
      setTimeout(() => {
        if (mediaRecorder.state === 'recording') {
          mediaRecorder.stop()
          setIsRecording(false)
        }
      }, 30000)

      // Store recorder reference for manual stop
      window.currentRecorder = mediaRecorder
    } catch (error) {
      console.error('Recording failed:', error)
      alert('Failed to start recording. Please check microphone permissions.')
    }
  }

  const stopRecording = () => {
    if (window.currentRecorder && window.currentRecorder.state === 'recording') {
      window.currentRecorder.stop()
      setIsRecording(false)
    }
  }

  const transcribeAudio = async (audioBlob) => {
    setIsLoading(true)
    try {
      const formData = new FormData()
      formData.append('audio', audioBlob, 'recording.wav')

      const response = await fetch('/api/dzongkha/speech-to-text', {
        method: 'POST',
        body: formData
      })

      if (response.ok) {
        const data = await response.json()
        setTranscription(data.transcription)
        
        // Auto-fill transcribed text
        if (data.transcription.text) {
          setDzongkhaText(data.transcription.text)
          if (language === 'dz') {
            setScript(data.transcription.text)
          }
        }
      }
    } catch (error) {
      console.error('Transcription failed:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const playDzongkhaTTS = async (text) => {
    if (!text.trim()) return

    try {
      const response = await fetch('/api/dzongkha/text-to-speech', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text })
      })

      if (response.ok) {
        const audioBlob = await response.blob()
        const audioUrl = URL.createObjectURL(audioBlob)
        const audio = new Audio(audioUrl)
        audio.play()
      }
    } catch (error) {
      console.error('TTS playback failed:', error)
    }
  }

  return (
    <Card className="w-full">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Languages className="w-5 h-5" />
          Dzongkha Language Support
        </CardTitle>
        <CardDescription>
          Create videos in Dzongkha with speech recognition and text-to-speech
        </CardDescription>
        
        {/* Capabilities Status */}
        {capabilities && (
          <div className="flex gap-2 mt-2">
            <Badge variant={capabilities.tts_available ? "default" : "secondary"}>
              {capabilities.tts_available ? "TTS Available" : "TTS Limited"}
            </Badge>
            <Badge variant={capabilities.asr_available ? "default" : "secondary"}>
              {capabilities.asr_available ? "ASR Available" : "ASR Limited"}
            </Badge>
            <Badge variant={capabilities.translation_available ? "default" : "secondary"}>
              {capabilities.translation_available ? "Translation Available" : "Translation Limited"}
            </Badge>
          </div>
        )}
      </CardHeader>
      
      <CardContent>
        <Tabs defaultValue="input" className="w-full">
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="input">Text Input</TabsTrigger>
            <TabsTrigger value="speech">Speech Input</TabsTrigger>
            <TabsTrigger value="translate">Translation</TabsTrigger>
          </TabsList>
          
          {/* Text Input Tab */}
          <TabsContent value="input" className="space-y-4">
            <div>
              <Label htmlFor="language-select">Language</Label>
              <Select value={language} onValueChange={handleLanguageChange}>
                <SelectTrigger className="mt-1">
                  <SelectValue placeholder="Select language" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="en">
                    <div className="flex items-center gap-2">
                      <Globe className="w-4 h-4" />
                      English
                    </div>
                  </SelectItem>
                  <SelectItem value="dz">
                    <div className="flex items-center gap-2">
                      <FileText className="w-4 h-4" />
                      རྫོང་ཁ (Dzongkha)
                    </div>
                  </SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div>
              <div className="flex items-center justify-between mb-2">
                <Label htmlFor="script-input">
                  {language === 'dz' ? 'Dzongkha Script' : 'English Script'}
                </Label>
                {language === 'dz' && (
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => playDzongkhaTTS(script)}
                    disabled={!script.trim() || !capabilities?.tts_available}
                  >
                    <Volume2 className="w-4 h-4 mr-1" />
                    Play
                  </Button>
                )}
              </div>
              
              <Textarea
                id="script-input"
                placeholder={
                  language === 'dz' 
                    ? "རྫོང་ཁའི་ཡིག་ཆ་འདིར་འབྲི་རོགས།..." 
                    : "Enter your script here..."
                }
                value={script}
                onChange={(e) => handleTextChange(e.target.value)}
                rows={6}
                className={`mt-1 ${language === 'dz' ? 'font-mono' : ''}`}
                style={language === 'dz' ? { direction: 'ltr', unicodeBidi: 'embed' } : {}}
              />
              
              {/* Validation for Dzongkha text */}
              {language === 'dz' && validation && (
                <div className="mt-2 flex items-center gap-2">
                  {validation.is_valid ? (
                    <Badge variant="default" className="bg-green-500">
                      <CheckCircle className="w-3 h-3 mr-1" />
                      Valid Dzongkha ({Math.round(validation.confidence * 100)}%)
                    </Badge>
                  ) : (
                    <Badge variant="secondary" className="bg-orange-500 text-white">
                      <AlertCircle className="w-3 h-3 mr-1" />
                      May not be Dzongkha ({Math.round(validation.confidence * 100)}%)
                    </Badge>
                  )}
                  <span className="text-sm text-gray-500">
                    {validation.character_count} characters, ~{validation.word_estimate} words
                  </span>
                </div>
              )}
            </div>
          </TabsContent>
          
          {/* Speech Input Tab */}
          <TabsContent value="speech" className="space-y-4">
            <div className="text-center space-y-4">
              <div>
                <Label>Record Dzongkha Speech</Label>
                <p className="text-sm text-gray-500 mt-1">
                  Click to start recording, speak in Dzongkha, then click stop
                </p>
              </div>
              
              <div className="flex justify-center gap-4">
                {!isRecording ? (
                  <Button
                    onClick={startRecording}
                    disabled={!capabilities?.asr_available || isLoading}
                    size="lg"
                  >
                    <Mic className="w-5 h-5 mr-2" />
                    Start Recording
                  </Button>
                ) : (
                  <Button
                    onClick={stopRecording}
                    variant="destructive"
                    size="lg"
                  >
                    <Square className="w-5 h-5 mr-2" />
                    Stop Recording
                  </Button>
                )}
              </div>
              
              {isRecording && (
                <div className="flex items-center justify-center gap-2 text-red-500">
                  <div className="w-3 h-3 bg-red-500 rounded-full animate-pulse"></div>
                  Recording... (max 30 seconds)
                </div>
              )}
              
              {/* Transcription Results */}
              {transcription && (
                <Card className="mt-4">
                  <CardHeader>
                    <CardTitle className="text-sm">Transcription Result</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-2">
                      <div className="p-3 bg-gray-50 rounded-lg">
                        <p className="font-mono">{transcription.text}</p>
                      </div>
                      {transcription.confidence && (
                        <Badge variant="outline">
                          Confidence: {Math.round(transcription.confidence * 100)}%
                        </Badge>
                      )}
                      {transcription.error && (
                        <Badge variant="secondary" className="bg-red-100 text-red-800">
                          {transcription.error}
                        </Badge>
                      )}
                    </div>
                  </CardContent>
                </Card>
              )}
            </div>
          </TabsContent>
          
          {/* Translation Tab */}
          <TabsContent value="translate" className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* English Input */}
              <div>
                <div className="flex items-center justify-between mb-2">
                  <Label>English Text</Label>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => translateText(englishText, 'en', 'dz')}
                    disabled={!englishText.trim() || isLoading}
                  >
                    Translate to Dzongkha →
                  </Button>
                </div>
                <Textarea
                  placeholder="Enter English text to translate..."
                  value={englishText}
                  onChange={(e) => setEnglishText(e.target.value)}
                  rows={4}
                />
              </div>
              
              {/* Dzongkha Output */}
              <div>
                <div className="flex items-center justify-between mb-2">
                  <Label>Dzongkha Text</Label>
                  <div className="flex gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => translateText(dzongkhaText, 'dz', 'en')}
                      disabled={!dzongkhaText.trim() || isLoading}
                    >
                      ← Translate to English
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => playDzongkhaTTS(dzongkhaText)}
                      disabled={!dzongkhaText.trim() || !capabilities?.tts_available}
                    >
                      <Volume2 className="w-4 h-4" />
                    </Button>
                  </div>
                </div>
                <Textarea
                  placeholder="རྫོང་ཁའི་ཡིག་ཆ་འདིར་སྣང་།..."
                  value={dzongkhaText}
                  onChange={(e) => setDzongkhaText(e.target.value)}
                  rows={4}
                  className="font-mono"
                  style={{ direction: 'ltr', unicodeBidi: 'embed' }}
                />
              </div>
            </div>
            
            {/* Translation Result */}
            {translation && (
              <Card>
                <CardHeader>
                  <CardTitle className="text-sm">Translation Result</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2">
                    <div className="p-3 bg-gray-50 rounded-lg">
                      <p>{translation.translated_text}</p>
                    </div>
                    {translation.error && (
                      <Badge variant="secondary" className="bg-orange-100 text-orange-800">
                        {translation.error}
                      </Badge>
                    )}
                  </div>
                </CardContent>
              </Card>
            )}
            
            {isLoading && (
              <div className="flex items-center justify-center py-4">
                <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600"></div>
                <span className="ml-2">Processing...</span>
              </div>
            )}
          </TabsContent>
        </Tabs>
      </CardContent>
    </Card>
  )
}

