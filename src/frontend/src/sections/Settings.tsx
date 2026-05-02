import { useState, useEffect } from 'react';
import { Save, RotateCcw, Loader2, Plus, X, FolderOpen } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import { Slider } from '@/components/ui/slider';
import { Separator } from '@/components/ui/separator';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { toast } from 'sonner';
import * as api from '@/services/api';

export function Settings() {
  const [config, setConfig] = useState<api.AppConfig | null>(null);
  const [hasChanges, setHasChanges] = useState(false);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [newLibraryPath, setNewLibraryPath] = useState('');

  useEffect(() => {
    api.getConfig().then(c => {
      setConfig(c);
      setLoading(false);
    }).catch(() => {
      toast.error('Failed to load config');
      setLoading(false);
    });
  }, []);

  const handleChange = <K extends keyof api.AppConfig>(key: K, value: api.AppConfig[K]) => {
    if (!config) return;
    setConfig({ ...config, [key]: value });
    setHasChanges(true);
  };

  const handleSave = async () => {
    if (!config) return;
    setSaving(true);
    try {
      const updated = await api.updateConfig(config);
      setConfig(updated);
      setHasChanges(false);
      toast.success('Settings saved successfully');
    } catch {
      toast.error('Failed to save settings');
    } finally {
      setSaving(false);
    }
  };

  const handleAddPath = () => {
    if (!newLibraryPath.trim() || !config) return;
    const paths = [...(config.libraryPaths || []), newLibraryPath.trim()];
    setConfig({ ...config, libraryPaths: paths });
    setNewLibraryPath('');
    setHasChanges(true);
  };

  const handleRemovePath = (index: number) => {
    if (!config) return;
    const paths = config.libraryPaths.filter((_, i) => i !== index);
    setConfig({ ...config, libraryPaths: paths });
    setHasChanges(true);
  };
    try {
      const defaults = await api.resetConfig();
      setConfig(defaults);
      setHasChanges(false);
      toast.info('Settings reset to defaults');
    } catch {
      toast.error('Failed to reset settings');
    }
  };

  if (loading || !config) {
    return (
      <div className="flex items-center justify-center h-full">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6 max-w-4xl">
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Settings</h1>
          <p className="text-muted-foreground">Configure download behavior and preferences</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={handleReset}>
            <RotateCcw className="h-4 w-4 mr-2" />
            Reset
          </Button>
          <Button onClick={handleSave} disabled={!hasChanges || saving}>
            {saving ? <Loader2 className="h-4 w-4 mr-2 animate-spin" /> : <Save className="h-4 w-4 mr-2" />}
            Save Changes
          </Button>
        </div>
      </div>

      <Tabs defaultValue="general" className="w-full">
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="general">General</TabsTrigger>
          <TabsTrigger value="download">Download</TabsTrigger>
          <TabsTrigger value="advanced">Advanced</TabsTrigger>
        </TabsList>

        <TabsContent value="general" className="space-y-4 mt-4">
          <Card>
            <CardHeader>
              <CardTitle>Output Settings</CardTitle>
              <CardDescription>Configure where downloaded manga is saved</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="output-dir">Output Directory</Label>
                <Input
                  id="output-dir"
                  value={config.outputDir}
                  onChange={(e) => handleChange('outputDir', e.target.value)}
                  placeholder="./manga_downloads"
                />
                <p className="text-xs text-muted-foreground">Directory where all downloaded manga will be saved</p>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Library Paths</CardTitle>
              <CardDescription>Additional folders to scan for manga in the Library reader</CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              {(config.libraryPaths || []).length > 0 ? (
                <div className="space-y-2">
                  {config.libraryPaths.map((path, i) => (
                    <div key={i} className="flex items-center gap-2 bg-muted rounded-md px-3 py-2">
                      <FolderOpen className="h-4 w-4 text-muted-foreground shrink-0" />
                      <span className="text-sm truncate flex-1">{path}</span>
                      <Button variant="ghost" size="icon" className="h-6 w-6" onClick={() => handleRemovePath(i)}>
                        <X className="h-3 w-3" />
                      </Button>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-sm text-muted-foreground">No additional library folders configured.</p>
              )}
              <div className="flex gap-2">
                <Input
                  placeholder="D:/manga/collection"
                  value={newLibraryPath}
                  onChange={(e) => setNewLibraryPath(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && handleAddPath()}
                />
                <Button variant="outline" size="icon" onClick={handleAddPath}>
                  <Plus className="h-4 w-4" />
                </Button>
              </div>
              <p className="text-xs text-muted-foreground">
                Point to existing manga folders (CBZ/ZIP archives in subdirectories). The download folder is always included.
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Naming Options</CardTitle>
              <CardDescription>Configure how manga folders and files are named</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <Label>Use English Title</Label>
                  <p className="text-sm text-muted-foreground">Use English title from series page instead of romanized URL</p>
                </div>
                <Switch checked={config.useEnglishTitle} onCheckedChange={(checked) => handleChange('useEnglishTitle', checked)} />
              </div>
              <Separator />
              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <Label>ZIP Archive Format</Label>
                  <p className="text-sm text-muted-foreground">Create .zip archives instead of .cbz (comic book zip)</p>
                </div>
                <Switch checked={config.zip} onCheckedChange={(checked) => handleChange('zip', checked)} />
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="download" className="space-y-4 mt-4">
          <Card>
            <CardHeader>
              <CardTitle>Download Mode</CardTitle>
              <CardDescription>Configure how chapters are downloaded</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <Label>Download Only Latest</Label>
                  <p className="text-sm text-muted-foreground">Only download chapters newer than the latest one already downloaded</p>
                </div>
                <Switch checked={config.latest} onCheckedChange={(checked) => handleChange('latest', checked)} />
              </div>
              <Separator />
              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <Label>Sequential Download</Label>
                  <p className="text-sm text-muted-foreground">Download images one by one instead of parallel</p>
                </div>
                <Switch checked={config.sequence} onCheckedChange={(checked) => handleChange('sequence', checked)} />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Rate Limiting</CardTitle>
              <CardDescription>Control download speed to avoid overwhelming the server</CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="space-y-3">
                <div className="flex justify-between">
                  <Label>Chapters Between Rate Limits (RLC)</Label>
                  <span className="text-sm font-medium">{config.rlc} chapters</span>
                </div>
                <Slider value={[config.rlc]} onValueChange={([value]) => handleChange('rlc', value)} min={1} max={50} step={1} />
              </div>
              <Separator />
              <div className="space-y-3">
                <div className="flex justify-between">
                  <Label>Max Sleep Time</Label>
                  <span className="text-sm font-medium">{config.maxSleep} seconds</span>
                </div>
                <Slider value={[config.maxSleep]} onValueChange={([value]) => handleChange('maxSleep', value)} min={10} max={300} step={10} />
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="advanced" className="space-y-4 mt-4">
          <Card>
            <CardHeader>
              <CardTitle>Retry Settings</CardTitle>
              <CardDescription>Configure retry behavior for failed downloads</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-3">
                <div className="flex justify-between">
                  <Label>Max Retries</Label>
                  <span className="text-sm font-medium">{config.maxRetries} attempts</span>
                </div>
                <Slider value={[config.maxRetries]} onValueChange={([value]) => handleChange('maxRetries', value)} min={1} max={10} step={1} />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Logging</CardTitle>
              <CardDescription>Configure logging verbosity</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <Label>Verbose Logging</Label>
                  <p className="text-sm text-muted-foreground">Enable detailed debug output for troubleshooting</p>
                </div>
                <Switch checked={config.verbose} onCheckedChange={(checked) => handleChange('verbose', checked)} />
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
