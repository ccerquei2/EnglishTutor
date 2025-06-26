// /src/components/VocabularyItem.tsx

import type { LessonItem } from '@/types/lesson';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { BookOpen } from 'lucide-react';

interface VocabularyProps {
  item: LessonItem;
  nativeLanguageCode: string;
}

export function VocabularyItem({ item, nativeLanguageCode }: VocabularyProps) {
  const { concept, translations } = item.content;

  // ### CORREÇÃO APLICADA AQUI ###
  // Garantimos um fallback para uma string informativa se a tradução não for encontrada.
  const relevantTranslation = translations?.[nativeLanguageCode] || "Tradução não disponível";

  return (
    <Card className="border-sky-200 bg-sky-50">
      <CardHeader className="flex flex-row items-center justify-between pb-2">
        <CardTitle className="text-lg font-medium text-sky-900">
          Novo Vocabulário
        </CardTitle>
        <BookOpen className="h-5 w-5 text-sky-600" />
      </CardHeader>
      <CardContent>
        <div className="flex items-end gap-4">
            <p className="text-4xl font-bold text-sky-800">{concept}</p>
            <p className="text-xl text-slate-600 pb-1">= {relevantTranslation}</p>
        </div>
      </CardContent>
    </Card>
  );
}