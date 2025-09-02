import { useState, useRef, useEffect } from 'react';
import { PencilIcon, CheckIcon, XMarkIcon as XIcon } from '@heroicons/react/24/outline';

interface ProcessNameEditorProps {
  name: string;
  onSave: (newName: string) => void;
  isDirty: boolean;
}

export const ProcessNameEditor: React.FC<ProcessNameEditorProps> = ({ name, onSave, isDirty }) => {
  const [isEditing, setIsEditing] = useState(false);
  const [currentName, setCurrentName] = useState(name);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    setCurrentName(name);
  }, [name]);

  useEffect(() => {
    if (isEditing && inputRef.current) {
      inputRef.current.focus();
      inputRef.current.select();
    }
  }, [isEditing]);

  const handleSave = () => {
    if (currentName.trim() !== '') {
      onSave(currentName);
      setIsEditing(false);
    }
  };

  const handleCancel = () => {
    setCurrentName(name);
    setIsEditing(false);
  };

  if (isEditing) {
    return (
      <div className="flex items-center space-x-2">
        <input
          ref={inputRef}
          type="text"
          value={currentName}
          onChange={(e) => setCurrentName(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter') handleSave();
            if (e.key === 'Escape') handleCancel();
          }}
          className="text-lg font-medium text-gray-900 bg-transparent border-b-2 border-blue-500 focus:outline-none"
        />
        <button onClick={handleSave} className="text-green-500 hover:text-green-700">
          <CheckIcon className="h-5 w-5" />
        </button>
        <button onClick={handleCancel} className="text-red-500 hover:text-red-700">
          <XIcon className="h-5 w-5" />
        </button>
      </div>
    );
  }

  return (
    <div className="flex items-center space-x-2">
      <h2 className="text-lg font-medium text-gray-900">{name}</h2>
      <button onClick={() => setIsEditing(true)} className="text-gray-500 hover:text-gray-700">
        <PencilIcon className="h-4 w-4" />
      </button>
    </div>
  );
};
