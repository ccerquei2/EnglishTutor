// /src/components/CulturalTipItem.tsx

import type { LessonItem } from '@/types/lesson';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Lightbulb } from 'lucide-react';

interface CulturalTipProps {
  item: LessonItem;
  nativeLanguageCode: string;
}

export function CulturalTipItem({ item, nativeLanguageCode }: CulturalTipProps) {
  const { title, tip } = item.content;

  // ### CORREÇÃO APLICADA AQUI ###
  // Garantimos um fallback final para uma string vazia se tudo falhar.
  const tipText = tip?.[nativeLanguageCode] || tip?.['en-US'] || '';

  return (
    <Card className="border-amber-200 bg-amber-50">
      <CardHeader className="flex flex-row items-center justify-between pb-2">
        <CardTitle className="text-lg font-medium text-amber-900">
          {title || "Dica Cultural"}
        </CardTitle>
        <Lightbulb className="h-5 w-5 text-amber-600" />
      </CardHeader>
      <CardContent>
        {/* Agora é seguro renderizar tipText, pois no pior caso será uma string vazia */}
        <p className="text-slate-800">{tipText}</p>
      </CardContent>
    </Card>
  );
}