'use client'

import { useEffect, useState, useCallback } from 'react'
import { toast } from 'sonner'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog'
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from '@/components/ui/alert-dialog'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { apiKeysApi, ApiKeyResponse } from '@/lib/api'
import { Plus, Copy, Trash2, Eye, EyeOff } from 'lucide-react'

export default function ApiKeysPage() {
  const [keys, setKeys] = useState<ApiKeyResponse[]>([])
  const [loading, setLoading] = useState(true)
  const [isCreating, setIsCreating] = useState(false)
  const [newKeyName, setNewKeyName] = useState('')
  const [newKeyRateLimit, setNewKeyRateLimit] = useState('60')
  const [createdKey, setCreatedKey] = useState<string | null>(null)
  const [dialogOpen, setDialogOpen] = useState(false)
  const [showCreatedKey, setShowCreatedKey] = useState(false)

  const fetchKeys = useCallback(async () => {
    try {
      const { data } = await apiKeysApi.list()
      setKeys(data)
    } catch {
      toast.error('Failed to load API keys')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchKeys()
  }, [fetchKeys])

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!newKeyName.trim()) return
    setIsCreating(true)
    try {
      const { data } = await apiKeysApi.create(newKeyName.trim(), parseInt(newKeyRateLimit, 10))
      setCreatedKey(data.key)
      setShowCreatedKey(true)
      await fetchKeys()
      toast.success('API key created')
    } catch {
      toast.error('Failed to create API key')
    } finally {
      setIsCreating(false)
    }
  }

  const handleRevoke = async (keyId: string) => {
    try {
      await apiKeysApi.revoke(keyId)
      setKeys((prev) => prev.filter((k) => k.id !== keyId))
      toast.success('API key revoked')
    } catch {
      toast.error('Failed to revoke API key')
    }
  }

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text).then(() => toast.success('Copied to clipboard'))
  }

  const handleDialogOpenChange = (open: boolean) => {
    setDialogOpen(open)
    if (!open) {
      setNewKeyName('')
      setNewKeyRateLimit('60')
      setCreatedKey(null)
      setShowCreatedKey(false)
    }
  }

  return (
    <div className="p-8">
      <div className="mb-8 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">API Keys</h1>
          <p className="text-slate-500 mt-1">Manage your API keys for accessing OpenClade</p>
        </div>
        <Dialog open={dialogOpen} onOpenChange={handleDialogOpenChange}>
          <DialogTrigger asChild>
            <Button className="bg-orange-500 hover:bg-orange-600">
              <Plus size={16} className="mr-2" />
              Create Key
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>{createdKey ? 'Key Created' : 'Create API Key'}</DialogTitle>
              <DialogDescription>
                {createdKey
                  ? 'Copy your API key now — it will not be shown again.'
                  : 'Give your key a name to identify it.'}
              </DialogDescription>
            </DialogHeader>

            {createdKey ? (
              <div className="space-y-4">
                <div className="bg-slate-100 rounded-lg p-3 flex items-center gap-2">
                  <code className="flex-1 text-sm font-mono break-all">
                    {showCreatedKey ? createdKey : '•'.repeat(Math.min(createdKey.length, 40))}
                  </code>
                  <Button
                    size="icon"
                    variant="ghost"
                    onClick={() => setShowCreatedKey((s) => !s)}
                  >
                    {showCreatedKey ? <EyeOff size={16} /> : <Eye size={16} />}
                  </Button>
                  <Button
                    size="icon"
                    variant="ghost"
                    onClick={() => copyToClipboard(createdKey)}
                  >
                    <Copy size={16} />
                  </Button>
                </div>
                <p className="text-sm text-amber-700 bg-amber-50 rounded-lg p-3">
                  ⚠️ Store this key securely. You won&apos;t be able to view it again.
                </p>
                <DialogFooter>
                  <Button onClick={() => setDialogOpen(false)}>Done</Button>
                </DialogFooter>
              </div>
            ) : (
              <form onSubmit={handleCreate} className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="key-name">Key Name</Label>
                  <Input
                    id="key-name"
                    placeholder="e.g. Production, Development"
                    value={newKeyName}
                    onChange={(e) => setNewKeyName(e.target.value)}
                    required
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="rate-limit">Rate Limit (req/min)</Label>
                  <Input
                    id="rate-limit"
                    type="number"
                    min="1"
                    max="1000"
                    value={newKeyRateLimit}
                    onChange={(e) => setNewKeyRateLimit(e.target.value)}
                  />
                </div>
                <DialogFooter>
                  <Button type="button" variant="outline" onClick={() => setDialogOpen(false)}>
                    Cancel
                  </Button>
                  <Button
                    type="submit"
                    className="bg-orange-500 hover:bg-orange-600"
                    disabled={isCreating}
                  >
                    {isCreating ? 'Creating…' : 'Create Key'}
                  </Button>
                </DialogFooter>
              </form>
            )}
          </DialogContent>
        </Dialog>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Your API Keys</CardTitle>
          <CardDescription>
            Use these keys to authenticate requests to the OpenClade API.
          </CardDescription>
        </CardHeader>
        <CardContent>
          {loading ? (
            <p className="text-slate-500 py-8 text-center">Loading keys…</p>
          ) : keys.length === 0 ? (
            <p className="text-slate-500 py-8 text-center">
              No API keys yet. Create one to get started.
            </p>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Name</TableHead>
                  <TableHead>Key</TableHead>
                  <TableHead>Rate Limit</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Created</TableHead>
                  <TableHead></TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {keys.map((key) => (
                  <TableRow key={key.id}>
                    <TableCell className="font-medium">{key.name}</TableCell>
                    <TableCell>
                      <code className="bg-slate-100 px-2 py-1 rounded text-sm">
                        {key.key_prefix}•••••••••••••
                      </code>
                    </TableCell>
                    <TableCell>{key.rate_limit} req/min</TableCell>
                    <TableCell>
                      <Badge variant={key.is_active ? 'default' : 'secondary'}>
                        {key.is_active ? 'Active' : 'Revoked'}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-slate-500">
                      {new Date(key.created_at).toLocaleDateString()}
                    </TableCell>
                    <TableCell>
                      {key.is_active && (
                        <AlertDialog>
                          <AlertDialogTrigger asChild>
                            <Button size="icon" variant="ghost" className="text-red-500 hover:text-red-700">
                              <Trash2 size={16} />
                            </Button>
                          </AlertDialogTrigger>
                          <AlertDialogContent>
                            <AlertDialogHeader>
                              <AlertDialogTitle>Revoke API Key</AlertDialogTitle>
                              <AlertDialogDescription>
                                This will permanently revoke the key &ldquo;{key.name}&rdquo;. Any applications
                                using it will stop working.
                              </AlertDialogDescription>
                            </AlertDialogHeader>
                            <AlertDialogFooter>
                              <AlertDialogCancel>Cancel</AlertDialogCancel>
                              <AlertDialogAction
                                className="bg-red-500 hover:bg-red-600"
                                onClick={() => handleRevoke(key.id)}
                              >
                                Revoke Key
                              </AlertDialogAction>
                            </AlertDialogFooter>
                          </AlertDialogContent>
                        </AlertDialog>
                      )}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
