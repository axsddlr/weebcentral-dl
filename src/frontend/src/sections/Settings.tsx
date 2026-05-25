import { useState, useEffect } from 'react';
import { Save, RotateCcw, Loader2, Plus, X, FolderOpen, LogOut, Clock } from 'lucide-react';
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
  const [maintenanceDryRun, setMaintenanceDryRun] = useState(true);
  const [runningMaintenance, setRunningMaintenance] = useState<null | 'add-covers' | 'migrate-covers'>(null);
  const [authToken, setAuthToken] = useState('');
  const [authEnabled, setAuthEnabled] = useState(false);
  const [authAuthenticated, setAuthAuthenticated] = useState(false);
  const [authLoggingIn, setAuthLoggingIn] = useState(false);

  useEffect(() => {
    api.getAuthStatus().then(s => {
      setAuthEnabled(s.enabled);
      setAuthAuthenticated(s.authenticated);
    }).catch(() => {});
  }, []);

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

  const handleReset = async () => {
    try {
      const defaults = await api.resetConfig();
      setConfig(defaults);
      setHasChanges(false);
      toast.info('Settings reset to defaults');
    } catch {
      toast.error('Failed to reset settings');
    }
  };

  const handleMaintenance = async (kind: 'add-covers' | 'migrate-covers') => {
    setRunningMaintenance(kind);
    try {
      const result = kind === 'add-covers'
        ? await api.addCoversMaintenance(maintenanceDryRun)
        : await api.migrateCoversMaintenance(maintenanceDryRun);

      const label = kind === 'add-covers' ? 'Add Covers' : 'Migrate Covers';
      const count = result.updated ?? result.migrated ?? 0;
      toast.success(`${label}: ${count} item(s) ${maintenanceDryRun ? 'would be' : 'were'} processed`);
    } catch {
      toast.error('Maintenance action failed');
    } finally {
      setRunningMaintenance(null);
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
                Add folders containing manga series (CBZ/ZIP archives in subdirectories). The download folder is always included.
                <br />
                <strong>Docker:</strong> use container paths (e.g. /app/library). Mount host folders as volumes in docker-compose.yml first.
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Tracker Settings</CardTitle>
              <CardDescription>Configure automatic checking for new chapters</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <div className="space-y-0.5">
                    <Label>Auto-Check Interval</Label>
                    <p className="text-sm text-muted-foreground">
                      How often the Docker watcher checks tracked manga for new chapters
                      (set to 0 to disable auto-checking)
                    </p>
                  </div>
                  <div className="flex items-center gap-2 shrink-0">
                    <Clock className="h-4 w-4 text-muted-foreground" />
                    <span className="text-sm font-medium min-w-[6rem] text-right">
                      {config.checkInterval === 0
                        ? 'Disabled'
                        : config.checkInterval < 60
                          ? `${config.checkInterval}m`
                          : config.checkInterval % 60 === 0
                            ? `${config.checkInterval / 60}h`
                            : `${Math.floor(config.checkInterval / 60)}h ${config.checkInterval % 60}m`}
                    </span>
                  </div>
                </div>
                <Slider
                  value={[config.checkInterval]}
                  onValueChange={([value]) => handleChange('checkInterval', value)}
                  min={0}
                  max={1440}
                  step={5}
                />
                <div className="flex justify-between text-xs text-muted-foreground">
                  <span>Off</span>
                  <span>15m</span>
                  <span>30m</span>
                  <span>1h</span>
                  <span>3h</span>
                  <span>6h</span>
                  <span>12h</span>
                  <span>24h</span>
                </div>
              </div>
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
              <Separator />
              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <Label>ComicInfo Metadata</Label>
                  <p className="text-sm text-muted-foreground">Write ComicInfo.xml into chapter archives for reader metadata support</p>
                </div>
                <Switch checked={config.comicinfo} onCheckedChange={(checked) => handleChange('comicinfo', checked)} />
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
              <Separator />
              <div className="space-y-3">
                <div className="flex justify-between">
                  <Label>Parallel Workers</Label>
                  <span className="text-sm font-medium">{config.parallelWorkers} workers</span>
                </div>
                <Slider value={[config.parallelWorkers]} onValueChange={([value]) => handleChange('parallelWorkers', value)} min={1} max={99} step={1} />
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

          <Card>
            <CardHeader>
              <CardTitle>API Authentication</CardTitle>
              <CardDescription>
                {authEnabled
                  ? (authAuthenticated ? 'Authenticated' : 'Not authenticated')
                  : 'No API_TOKEN configured on the server'}
              </CardDescription>
            </CardHeader>
            <CardContent>
              {authEnabled && !authAuthenticated && (
                <div className="space-y-3">
                  <div className="space-y-2">
                    <Label htmlFor="auth-token">Enter API Token</Label>
                    <div className="flex gap-2">
                      <Input
                        id="auth-token"
                        type="password"
                        value={authToken}
                        onChange={(e) => setAuthToken(e.target.value)}
                        placeholder="Enter your API token"
                        onKeyDown={(e) => {
                          if (e.key === 'Enter' && authToken && !authLoggingIn) {
                            setAuthLoggingIn(true);
                            api.login(authToken).then(() => {
                              setAuthAuthenticated(true);
                              setAuthToken('');
                              toast.success('Authenticated successfully');
                            }).catch(() => toast.error('Invalid token')).finally(() => setAuthLoggingIn(false));
                          }
                        }}
                      />
                      <Button
                        onClick={() => {
                          setAuthLoggingIn(true);
                          api.login(authToken).then(() => {
                            setAuthAuthenticated(true);
                            setAuthToken('');
                            toast.success('Authenticated successfully');
                          }).catch(() => toast.error('Invalid token')).finally(() => setAuthLoggingIn(false));
                        }}
                        disabled={!authToken || authLoggingIn}
                      >
                        {authLoggingIn ? <Loader2 className="h-4 w-4 animate-spin" /> : 'Login'}
                      </Button>
                    </div>
                  </div>
                  <p className="text-xs text-muted-foreground">
                    Token is stored in an httpOnly cookie — not accessible to JavaScript.
                    Set <code>API_TOKEN</code> in the server's <code>.env</code> to enable authentication.
                  </p>
                </div>
              )}
              {authEnabled && authAuthenticated && (
                <div className="space-y-3">
                  <p className="text-sm text-green-600 dark:text-green-400">Authenticated</p>
                  <Button variant="outline" onClick={async () => {
                    await api.logout();
                    setAuthAuthenticated(false);
                    toast.success('Logged out');
                  }}>
                    <LogOut className="h-4 w-4 mr-2" />
                    Logout
                  </Button>
                </div>
              )}
              {!authEnabled && (
                <p className="text-sm text-muted-foreground">
                  Authentication is not enabled. Set <code>API_TOKEN</code> in <code>.env</code> to protect the API.
                </p>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Library Maintenance</CardTitle>
              <CardDescription>Run cover maintenance on the current output library</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <Label>Dry Run</Label>
                  <p className="text-sm text-muted-foreground">Preview changes before writing to disk</p>
                </div>
                <Switch checked={maintenanceDryRun} onCheckedChange={setMaintenanceDryRun} />
              </div>
              <Separator />
              <div className="flex flex-wrap gap-2">
                <Button
                  variant="outline"
                  onClick={() => handleMaintenance('add-covers')}
                  disabled={runningMaintenance !== null}
                >
                  {runningMaintenance === 'add-covers' ? 'Running...' : 'Add Covers'}
                </Button>
                <Button
                  variant="outline"
                  onClick={() => handleMaintenance('migrate-covers')}
                  disabled={runningMaintenance !== null}
                >
                  {runningMaintenance === 'migrate-covers' ? 'Running...' : 'Migrate Covers'}
                </Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
