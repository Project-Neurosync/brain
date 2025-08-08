"use client";

import React, { useState, useEffect } from 'react';
import { ChevronDown, Folder, Globe } from 'lucide-react';

interface Project {
  id: string;
  name: string;
  description?: string;
}

interface ProjectSelectorProps {
  selectedProjectId: string | null;
  onProjectChange: (projectId: string | null) => void;
}

export function ProjectSelector({ selectedProjectId, onProjectChange }: ProjectSelectorProps) {
  const [projects, setProjects] = useState<Project[]>([]);
  const [isOpen, setIsOpen] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchProjects();
  }, []);

  const fetchProjects = async () => {
    try {
      const response = await fetch('/api/v1/projects/', {
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (response.ok) {
        const data = await response.json();
        setProjects(data || []);
      } else {
        console.error('Failed to fetch projects');
      }
    } catch (error) {
      console.error('Error fetching projects:', error);
    } finally {
      setLoading(false);
    }
  };

  const selectedProject = projects.find(p => p.id === selectedProjectId);

  const handleProjectSelect = (projectId: string | null) => {
    onProjectChange(projectId);
    setIsOpen(false);
  };

  if (loading) {
    return (
      <div className="w-48 h-8 bg-gray-200 animate-pulse rounded-md"></div>
    );
  }

  return (
    <div className="relative">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center space-x-2 px-3 py-2 border border-gray-300 rounded-md hover:bg-gray-50 focus:ring-2 focus:ring-blue-500 focus:border-transparent min-w-[200px]"
      >
        {selectedProject ? (
          <>
            <Folder className="w-4 h-4 text-blue-600" />
            <span className="flex-1 text-left truncate">{selectedProject.name}</span>
          </>
        ) : (
          <>
            <Globe className="w-4 h-4 text-gray-400" />
            <span className="flex-1 text-left text-gray-500">All Projects</span>
          </>
        )}
        <ChevronDown className={`w-4 h-4 text-gray-400 transition-transform ${isOpen ? 'rotate-180' : ''}`} />
      </button>

      {isOpen && (
        <div className="absolute top-full left-0 right-0 mt-1 bg-white border border-gray-200 rounded-md shadow-lg z-50 max-h-60 overflow-y-auto">
          <button
            onClick={() => handleProjectSelect(null)}
            className={`w-full flex items-center space-x-2 px-3 py-2 text-left hover:bg-gray-50 ${
              !selectedProjectId ? 'bg-blue-50 text-blue-700' : 'text-gray-700'
            }`}
          >
            <Globe className="w-4 h-4" />
            <div>
              <div className="font-medium">All Projects</div>
              <div className="text-xs text-gray-500">Search across all your data</div>
            </div>
          </button>

          {projects.length === 0 ? (
            <div className="px-3 py-2 text-gray-500 text-sm">
              No projects found. Create a project to get started.
            </div>
          ) : (
            projects.map((project) => (
              <button
                key={project.id}
                onClick={() => handleProjectSelect(project.id)}
                className={`w-full flex items-center space-x-2 px-3 py-2 text-left hover:bg-gray-50 ${
                  selectedProjectId === project.id ? 'bg-blue-50 text-blue-700' : 'text-gray-700'
                }`}
              >
                <Folder className="w-4 h-4" />
                <div className="flex-1 min-w-0">
                  <div className="font-medium truncate">{project.name}</div>
                  {project.description && (
                    <div className="text-xs text-gray-500 truncate">{project.description}</div>
                  )}
                </div>
              </button>
            ))
          )}
        </div>
      )}

      {/* Backdrop to close dropdown */}
      {isOpen && (
        <div
          className="fixed inset-0 z-40"
          onClick={() => setIsOpen(false)}
        />
      )}
    </div>
  );
}
