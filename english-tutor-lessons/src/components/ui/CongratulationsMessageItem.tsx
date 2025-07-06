// /src/components/ui/CongratulationsMessageItem.tsx

import { PartyPopper } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from "./card";
import { LearningUnit } from '@/types/learning-unit'; // Supondo que você tenha um tipo

interface CongratulationsMessageProps {
  item: LearningUnit;
  nativeLanguageCode: string;
}

export function CongratulationsMessageItem({ item, nativeLanguageCode }: CongratulationsMessageProps) {
  // O objeto 'item.content' contém 'title' e 'message'.
  // 'message' é um objeto com os códigos de idioma.
  const { title, message } = item.content || { title: 'Parabéns!', message: {} };

  // Usamos optional chaining e fallback para segurança.
  const contentText = message?.[nativeLanguageCode] || message?.['en-US'] || 'Você completou esta etapa!';

  return (
    <Card className="bg-blue-50 border-blue-200">
      <CardHeader>
        <div className="flex items-center gap-2">
          <PartyPopper className="h-6 w-6 text-blue-600" />
          <CardTitle className="text-blue-800">{title}</CardTitle>
        </div>
      </CardHeader>
      <CardContent>
        <p className="text-lg text-blue-700">{contentText}</p>
      </CardContent>
    </Card>
  );
}