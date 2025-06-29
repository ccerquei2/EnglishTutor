// /src/components/ui/CulturalTipItem.tsx

import type { LessonItem } from '@/types/lesson';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './card';
import { Globe } from 'lucide-react';

interface CulturalTipProps {
  item: LessonItem;
  nativeLanguageCode: string;
}

export function CulturalTipItem({ item, nativeLanguageCode }: CulturalTipProps) {
  const { title, content } = item.content;
  const contentText = content[nativeLanguageCode] || content['en-US'];

  return (
    <Card className="bg-purple-50 border-purple-200">
      <CardHeader>
        <div className="flex items-center gap-2">
            <Globe className="h-6 w-6 text-purple-600" />
            <CardTitle>{title}</CardTitle>
        </div>
        <CardDescription>Dica Cultural</CardDescription>
      </CardHeader>
      <CardContent>
        <p className="italic">{contentText}</p>
      </CardContent>
    </Card>
  );
}