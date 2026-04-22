"use client";

import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { ModelTab } from "./model-tab";
import { RetrievalTab } from "./retrieval-tab";
import { DisplayTab } from "./display-tab";

interface Props {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function SettingsSheet({ open, onOpenChange }: Props) {
  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent className="w-[420px] sm:w-[460px] overflow-y-auto">
        <SheetHeader>
          <SheetTitle className="text-base">Settings</SheetTitle>
        </SheetHeader>

        <Tabs defaultValue="model" className="mt-6">
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="model">Model</TabsTrigger>
            <TabsTrigger value="retrieval">Retrieval</TabsTrigger>
            <TabsTrigger value="display">Display</TabsTrigger>
          </TabsList>

          <TabsContent value="model" className="mt-4 space-y-5">
            <ModelTab />
          </TabsContent>

          <TabsContent value="retrieval" className="mt-4 space-y-5">
            <RetrievalTab />
          </TabsContent>

          <TabsContent value="display" className="mt-4 space-y-5">
            <DisplayTab />
          </TabsContent>
        </Tabs>
      </SheetContent>
    </Sheet>
  );
}
