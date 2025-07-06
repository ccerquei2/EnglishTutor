// /english-tutor-lessons/src/components/ui/CulturalTipItem.tsx

import { Globe } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "./card";
import { LearningUnit } from '@/types/learning-unit'; // Supondo que você tenha um tipo

interface CulturalTipProps {
  item: LearningUnit;
  nativeLanguageCode: string;
}

export function CulturalTipItem({ item, nativeLanguageCode }: CulturalTipProps) {
  // CORREÇÃO:
  // O objeto 'item.content' para 'cultural_tip' contém 'title' e 'tip'.
  // Desestruturamos 'tip' em vez de um 'content' inexistente.
  // Adicionamos um fallback `{}` para evitar crash se item.content for nulo.
  const { title, tip } = item.content || { title: 'Dica Cultural', tip: {} };

  // BOA PRÁTICA:
  // Usamos optional chaining (?.) para acessar as propriedades de 'tip'.
  // Isso evita o erro se 'tip' for nulo ou se o código do idioma não existir.
  // Também adicionamos um texto de fallback final.
  const contentText = tip?.[nativeLanguageCode] || tip?.['en-US'] || 'Conteúdo da dica indisponível.';

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