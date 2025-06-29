// /src/components/ui/DialogueItem.tsx

import type { LessonItem } from '@/types/lesson';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './card';
import { cn } from '@/lib/utils';

interface DialogueProps {
  item: LessonItem;
}

export function DialogueItem({ item }: DialogueProps) {
  const { title, lines } = item.content;

  return (
    <Card className="bg-green-50 border-green-200">
      <CardHeader>
        <CardTitle>{title || 'Diálogo'}</CardTitle>
        <CardDescription>Prática de Conversação</CardDescription>
      </CardHeader>
      <CardContent className="space-y-3">
        {lines.map((line: { speaker: string; sentence: string }, index: number) => (
          <div
            key={index}
            className={cn(
              'flex w-full',
              line.speaker === 'A' ? 'justify-start' : 'justify-end'
            )}
          >
            <div
              className={cn(
                'max-w-[80%] rounded-lg px-4 py-2',
                line.speaker === 'A'
                  ? 'bg-white text-gray-900'
                  : 'bg-primary text-primary-foreground'
              )}
            >
              <p className="text-sm">
                <span className="font-bold mr-2">{line.speaker}:</span>
                {line.sentence}
              </p>
            </div>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}