/**
 * Data Management Page
 * Combines sync status monitoring and file upload functionality
 */

'use client'

import { useState } from 'react'
import { motion } from 'framer-motion'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../../../../../components/ui/tabs'
import { DataSyncStatus } from '../../../../../components/sync/DataSyncStatus'
import { FileUpload } from '../../../../../components/upload/FileUpload'
import { Database, Upload, Activity, FileText } from 'lucide-react'

interface DataPageProps {
  params: {
    id: string
  }
}

export default function DataPage({ params }: DataPageProps) {
  const [activeTab, setActiveTab] = useState('sync')
  const projectId = params.id

  const handleUploadComplete = (files: any[]) => {
    console.log('Files uploaded:', files)
    // Handle successful uploads - could trigger a sync or update UI
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Data Management</h1>
        <p className="text-gray-600 mt-2">
          Monitor synchronization status and upload documents for AI processing
        </p>
      </div>

      {/* Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
        <TabsList className="grid w-full grid-cols-2">
          <TabsTrigger value="sync" className="flex items-center gap-2">
            <Activity className="h-4 w-4" />
            Sync Status
          </TabsTrigger>
          <TabsTrigger value="upload" className="flex items-center gap-2">
            <Upload className="h-4 w-4" />
            File Upload
          </TabsTrigger>
        </TabsList>

        <TabsContent value="sync" className="space-y-6">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3 }}
          >
            <DataSyncStatus projectId={projectId} />
          </motion.div>
        </TabsContent>

        <TabsContent value="upload" className="space-y-6">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3 }}
          >
            <div className="bg-white rounded-lg border border-gray-200 p-6">
              <div className="flex items-center gap-3 mb-6">
                <div className="p-2 bg-blue-100 rounded-lg">
                  <FileText className="h-5 w-5 text-blue-600" />
                </div>
                <div>
                  <h2 className="text-xl font-semibold text-gray-900">Document Upload</h2>
                  <p className="text-gray-600">
                    Upload documents to enhance your project's knowledge base
                  </p>
                </div>
              </div>
              
              <FileUpload
                projectId={projectId}
                onUploadComplete={handleUploadComplete}
                maxFiles={20}
                maxSize={100}
                acceptedTypes={[
                  '.pdf', '.doc', '.docx', '.txt', '.md', '.rtf',
                  '.png', '.jpg', '.jpeg', '.gif', '.webp',
                  '.csv', '.xlsx', '.json', '.xml'
                ]}
              />
            </div>
          </motion.div>
        </TabsContent>
      </Tabs>
    </div>
  )
}
