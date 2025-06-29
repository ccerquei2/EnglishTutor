// /src/components/ui/GrammarRuleItem.tsx

import type { LessonItem } from '@/types/lesson';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './card';

interface GrammarRuleProps {
  item: LessonItem;
}

export function GrammarRuleItem({ item }: GrammarRuleProps) {
  const { rule_name, explanation, positive_form } = item.content;
  const explanationText = explanation['pt-BR'] || explanation['en-US'];

  return (
    <Card className="bg-blue-50 border-blue-200">
      <CardHeader>
        <CardTitle>{rule_name}</CardTitle>
        <CardDescription>Regra Gramatical</CardDescription>
      </CardHeader>
      <CardContent>
        <p className="mb-4">{explanationText}</p>
        <div className="bg-white p-3 rounded-md border">
          <p className="font-mono text-sm text-slate-700">{positive_form}</p>
        </div>
      </CardContent>
    </Card>
  );
}