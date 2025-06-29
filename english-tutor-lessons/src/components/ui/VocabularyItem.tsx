// /src/components/ui/VocabularyItem.tsx

import type { LessonItem } from '@/types/lesson';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './card';

interface VocabularyProps {
  item: LessonItem;
  nativeLanguageCode: string;
}

export function VocabularyItem({ item, nativeLanguageCode }: VocabularyProps) {
  const { concept, translations } = item.content;
  const translationText = translations[nativeLanguageCode] || translations['en-US'];

  return (
    <Card className="bg-yellow-50 border-yellow-200">
      <CardHeader>
        <CardTitle>{concept}</CardTitle>
        <CardDescription>Novo Vocabulário</CardDescription>
      </CardHeader>
      <CardContent>
        <p className="text-lg">
          <span className="font-semibold">Tradução:</span> {translationText}
        </p>
      </CardContent>
    </Card>
  );
}