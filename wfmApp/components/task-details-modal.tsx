"use client";

import React from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { MapPin, Phone, Mail, User, FileText, Image, Calendar, Clock, AlertCircle } from 'lucide-react';

interface TaskDetailsModalProps {
  task: any;
  isOpen: boolean;
  onClose: () => void;
}

const TaskDetailsModal: React.FC<TaskDetailsModalProps> = ({ task, isOpen, onClose }) => {
  if (!task) return null;

  // Mock customer and materials data based on the screenshot
  const customerDetails = {
    name: "Rajesh Kumar",
    phone: "+91 1234567890",
    email: "rajeshkumar@gmail.com"
  };

  const materials = [
    { name: "Duct", quantity: "200ft" },
    { name: "Fiber Cable", quantity: "800ft" },
    { name: "Splice Closures", quantity: "800ft" }
  ];

  const attachments = [
    { name: "Site plan.pdf", type: "PDF" },
    { name: "Work Order.pdf", type: "PDF" }
  ];

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'urgent': return 'destructive';
      case 'high': return 'secondary';
      case 'medium': return 'outline';
      case 'low': return 'outline';
      default: return 'outline';
    }
  };

  const formatDate = (dateString: string) => {
    if (!dateString) return 'Not set';
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-7xl w-[95vw] max-h-[90vh] overflow-y-auto">
        <DialogHeader className="pb-4">
          <DialogTitle className="text-2xl font-bold">Task Details</DialogTitle>
          <div className="text-sm text-muted-foreground">{task.id}</div>
        </DialogHeader>

        {/* Task Header Section */}
        <div className="mb-6">
          <div className="flex items-start justify-between flex-wrap gap-4 mb-4">
            <div>
              <h2 className="text-2xl font-bold mb-2">{task.name}</h2>
              <div className="flex flex-wrap items-center gap-4 text-sm text-muted-foreground">
                <div className="flex items-center space-x-2">
                  <MapPin className="h-4 w-4" />
                  <span>{task.location || '456 Maple Ave, Lakewood, TX'}</span>
                </div>
                <div className="flex items-center space-x-2">
                  <Calendar className="h-4 w-4" />
                  <span>Due: 29/08/25</span>
                </div>
                <div className="flex items-center space-x-2">
                  <Clock className="h-4 w-4" />
                  <span>Estimated: 60 minutes</span>
                </div>
              </div>
            </div>
            <Badge variant={getPriorityColor(task.priority)} className="text-lg px-4 py-2">
              {task.priority}
            </Badge>
          </div>
        </div>

        {/* Main Content Grid */}
        <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
          {/* Left Column - Map and Attachments */}
          <div className="xl:col-span-2 space-y-6">
            {/* Map Section */}
            <Card>
              <CardContent className="p-6">
                <div className="bg-gray-100 rounded-lg h-64 flex items-center justify-center relative">
                  <div className="absolute inset-0 flex items-center justify-center">
                    {/* Mock map with location pin */}
                    <div className="relative w-full h-full">
                      {/* Map background with some geometric shapes to simulate map */}
                      <div className="absolute top-8 left-12 w-16 h-12 bg-gray-300 rounded"></div>
                      <div className="absolute top-16 right-20 w-20 h-8 bg-gray-300 rounded"></div>
                      <div className="absolute bottom-12 left-20 w-12 h-16 bg-gray-300 rounded"></div>
                      <div className="absolute bottom-16 right-16 w-16 h-12 bg-gray-300 rounded"></div>
                      
                      {/* Location pin in center */}
                      <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2">
                        <MapPin className="h-8 w-8 text-orange-500" />
                      </div>
                      
                      {/* Map lines to simulate streets */}
                      <svg className="absolute inset-0 w-full h-full" viewBox="0 0 400 200">
                        <path d="M50 50 L350 80 L300 150 L100 120 Z" stroke="#ccc" strokeWidth="2" fill="none" />
                        <path d="M100 30 L300 180" stroke="#ccc" strokeWidth="2" fill="none" />
                        <path d="M30 100 L370 100" stroke="#ccc" strokeWidth="2" fill="none" />
                      </svg>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Attachments Section */}
            <Card>
              <CardContent className="p-6">
                <Tabs defaultValue="attachments" className="w-full">
                  <TabsList className="mb-6">
                    <TabsTrigger value="attachments" className="px-6 py-2">Attachments</TabsTrigger>
                    <TabsTrigger value="photos" className="px-6 py-2">Photos and videos</TabsTrigger>
                  </TabsList>
                  
                  <TabsContent value="attachments">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      {attachments.map((attachment, index) => (
                        <div key={index} className="border rounded-lg p-4 flex items-center space-x-3 hover:bg-gray-50 cursor-pointer transition-colors">
                          <FileText className="h-10 w-10 text-orange-500" />
                          <div>
                            <div className="font-medium text-base">{attachment.name}</div>
                            <div className="text-sm text-muted-foreground">{attachment.type}</div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </TabsContent>
                  
                  <TabsContent value="photos">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      {attachments.map((attachment, index) => (
                        <div key={index} className="border rounded-lg p-4 flex items-center space-x-3 hover:bg-gray-50 cursor-pointer transition-colors">
                          <Image className="h-10 w-10 text-orange-500" />
                          <div>
                            <div className="font-medium text-base">{attachment.name}</div>
                            <div className="text-sm text-muted-foreground">{attachment.type}</div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </TabsContent>
                </Tabs>
              </CardContent>
            </Card>
          </div>

          {/* Right Column - Customer Details & Materials */}
          <div className="space-y-6">
            {/* Customer Details */}
            <Card>
              <CardHeader className="pb-4">
                <CardTitle className="flex items-center space-x-2 text-xl">
                  <User className="h-6 w-6 text-orange-500" />
                  <span>Customer Details</span>
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <div className="font-semibold text-lg">{customerDetails.name}</div>
                </div>
                <div className="flex items-center space-x-3">
                  <Phone className="h-5 w-5 text-muted-foreground" />
                  <span className="text-base">{customerDetails.phone}</span>
                </div>
                <div className="flex items-center space-x-3">
                  <Mail className="h-5 w-5 text-muted-foreground" />
                  <span className="text-base">{customerDetails.email}</span>
                </div>
              </CardContent>
            </Card>

            {/* Materials */}
            <Card>
              <CardHeader className="pb-4">
                <CardTitle className="text-xl">Materials</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {materials.map((material, index) => (
                    <div key={index} className="flex justify-between items-center py-2 border-b border-gray-100 last:border-b-0">
                      <span className="text-base">{material.name}</span>
                      <span className="text-base font-semibold">{material.quantity}</span>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            {/* Task Information */}
            <Card>
              <CardHeader className="pb-4">
                <CardTitle className="text-xl">Task Information</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="flex justify-between items-center">
                  <span className="text-muted-foreground">Status:</span>
                  <Badge variant="outline" className="text-sm">{task.status}</Badge>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-muted-foreground">Type:</span>
                  <span className="text-sm">{task.type}</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-muted-foreground">Process:</span>
                  <span className="text-sm">{task.process_definition_key}</span>
                </div>
                {task.technician_name && (
                  <div className="flex justify-between items-center">
                    <span className="text-muted-foreground">Technician:</span>
                    <span className="text-sm">{task.technician_name}</span>
                  </div>
                )}
                {task.lead_name && (
                  <div className="flex justify-between items-center">
                    <span className="text-muted-foreground">Lead:</span>
                    <span className="text-sm">{task.lead_name}</span>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Required Skills */}
            {task.required_skills && task.required_skills.length > 0 && (
              <Card>
                <CardHeader className="pb-4">
                  <CardTitle className="text-xl">Required Skills</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="flex flex-wrap gap-2">
                    {task.required_skills.map((skill: string, index: number) => (
                      <Badge key={index} variant="secondary" className="text-sm">
                        {skill.replace('_', ' ')}
                      </Badge>
                    ))}
                  </div>
                </CardContent>
              </Card>
            )}
          </div>
        </div>

        {/* Bottom Action Button */}
        <div className="mt-8 pt-6 border-t">
          <Button className="w-full bg-orange-500 hover:bg-orange-600 text-white py-4 text-lg font-semibold">
            Assign Technician
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
};

export default TaskDetailsModal;
